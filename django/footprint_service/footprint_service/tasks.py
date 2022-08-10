# footprint_service/tasks.py

from django.utils import timezone
from django.conf import settings
from celery import shared_task
from footprint_service.models import Footprint
import requests
import numpy as np
from skimage import io
from io import BytesIO

import torch
from hisup.config import cfg
from hisup.detector import get_pretrained_model
from hisup.dataset.build import build_transform
from hisup.utils.comm import to_single_device

from shapely.geometry import MultiPolygon, Polygon, Point, box, mapping
from shapely.geometry.polygon import orient
from shapely.validation import make_valid
from pyproj import Geod
import geopandas as gpd
import pandas as pd
import json
import traceback


@shared_task()
def process_item(pk):
    try:
        fobj = Footprint.objects.get(pk=pk)
        fobj.status = 'PROCESSING'
        fobj.started = timezone.now()
        fobj.save()

        img_array, bounds = request_satellite_imagery(fobj.longitude, fobj.latitude, fobj.zoom_level)
        analysis_area_bbox = box(*bounds)
        # convert bbox to valid geojson via shapely
        fobj.bbox_analysis_geojson = json.dumps(mapping(analysis_area_bbox))
        # check validity of satellite image
        fobj.is_valid_img = is_valid_img_check(img_array)
        if fobj.is_valid_img:
            # use inria as pretrained model dataset. crowdai is alternative, but
            # seems to perform worse for our usecase.
            polys_pred_pixels = infer_polygons_from_image(img_array, dataset='inria')
            polys_shapely = to_shapely_polygons(polys_pred_pixels, analysis_area_bbox, img_array)
            geojson = to_geojson(polys_shapely, analysis_area_bbox, fobj.longitude, fobj.latitude)
            fobj.footprints_geojson = geojson

        fobj.status = 'SUCCESS'
        fobj.finished = timezone.now()
        fobj.save()
    except Exception as e:
        fobj.finished = timezone.now()
        fobj.error_traceback = traceback.format_exc()
        fobj.status = 'FAILURE'
        fobj.save()
        raise e


def request_satellite_imagery(longitude, latitude, zoom_level):
    # request satellite image
    centerPoint = f'{latitude},{longitude}'
    imagerySet = 'Aerial'
    zoomLevel = zoom_level
    mapSize = '512,512'
    BingMapsKey = settings.BING_KEY
    url = f'https://dev.virtualearth.net/REST/v1/Imagery/Map/{imagerySet}/{centerPoint}/{zoomLevel}?mapSize={mapSize}&format=png&key={BingMapsKey}'
    r = requests.get(url)
    r.raise_for_status()
    img_array = io.imread(BytesIO(r.content))[:, :, :3]

    # Obtain bounds of analysis area from metadata. Used later to calculate
    # polygon coordinates in epsg4326.
    metadata = requests.get(url + '&mapMetadata=1').json()['resourceSets'][0]['resources'][0]
    bounds = metadata['bbox']
    # Perform extra step to get bounds in more sensible xmin, ymin, xmax, ymax format.
    # From Bing static maps api docs: "A geographic area that contains the location.
    # A bounding box contains SouthLatitude, WestLongitude, NorthLatitude, and EastLongitude
    # values in units of degrees."
    bounds[1], bounds[0], bounds[3], bounds[2] = bounds
    return img_array, bounds


def is_valid_img_check(img_array):
    """
    For some places / zoomlevels where no imagery is available,
    Bing API returns a greyish image with camera icon watermarks.
    We use a very empirical / hacky way of finding these images by looking
    at the most common pixel value of band 2, which is 242 for these.
    """
    vals, counts = np.unique(img_array[:,:,1], return_counts=True)
    index = np.argmax(counts)
    return vals[index] != 242


MODEL_CACHE = {}
def get_pretrained_model_cached(cfg, dataset, device, pretrained):
    """
    Sadly cfg object is not hashable and we cannot easily use functools cache.
    Improvise a cache here as dictionary using the most important
    characteristics from a quick look over HiSup code base.
    """
    global MODEL_CACHE

    model_fingerprint = (
        cfg.MODEL.NAME,
        cfg.DATASETS.ORIGIN.HEIGHT,
        cfg.DATASETS.ORIGIN.WIDTH,
        cfg.DATASETS.TARGET.HEIGHT,
        cfg.DATASETS.TARGET.WIDTH,
        dataset,
        device,
        pretrained
    )

    if model_fingerprint not in MODEL_CACHE:
        MODEL_CACHE[model_fingerprint] = get_pretrained_model(cfg, dataset, device, pretrained)
    return MODEL_CACHE[model_fingerprint]


def infer_polygons_from_image(img_array, dataset):
    """
    Infer building footprints from image ndarray using the
    HiSup model (https://github.com/SarahwXU/HiSup). Returns a nested
    array of polygons using the pixel space of the image.
    """

    assert img_array.shape == (512, 512, 3)

    device = cfg.MODEL.DEVICE
    if not torch.cuda.is_available():
        device = 'cpu'

    H, W = img_array.shape[:2]
    img_mean, img_std = [], []
    for i in range(img_array.shape[-1]):
        pixels = img_array[:, :, i].ravel()
        img_mean.append(np.mean(pixels))
        img_std.append(np.std(pixels))
    cfg.DATASETS.IMAGE.PIXEL_MEAN = img_mean
    cfg.DATASETS.IMAGE.PIXEL_STD  = img_std
    cfg.DATASETS.ORIGIN.HEIGHT = H
    cfg.DATASETS.ORIGIN.WIDTH = W

    model = get_pretrained_model_cached(cfg, dataset, device, pretrained=True)

    model = model.to(device)
    return get_inference_output(cfg, model, img_array, device)


def get_inference_output(cfg, model, img_array, device):
    transform = build_transform(cfg)
    image_tensor = transform(img_array.astype(float))[None].to(device)
    meta = {
        'height': img_array.shape[0],
        'width': img_array.shape[1],
    }
    with torch.no_grad():
        output, _ = model(image_tensor, [meta])
        output = to_single_device(output, 'cpu')
        # Predicted polygons are returned in batches, so flatten output list.
        polys_pred_flat = []
        for p in output['polys_pred']:
            polys_pred_flat.extend(p)
    return polys_pred_flat


def to_shapely_polygons(polys_pred_pixels, analysis_area_bbox, img_array):
    img_height, img_width = img_array.shape[:2]
    lon_min, lat_min, lon_max, lat_max = analysis_area_bbox.bounds
    to_lon = lambda x: x / img_width * (lon_max - lon_min) + lon_min
    # Subtract y from image height because "top" (y=0) is at top in matrix/image.
    to_lat = lambda y: (img_height - y) / img_height * (lat_max - lat_min) + lat_min

    polygons_shapely = []
    for polygon in polys_pred_pixels:
        vertices_4326 = []
        for (x,y) in polygon:
            vertices_4326.append([to_lon(x), to_lat(y)]) #xy
        polygon_shapely = orient(Polygon(vertices_4326)) # properly orient polygon
        if not polygon_shapely.is_valid:
            polygon_shapely = make_valid(polygon_shapely)
            if not polygon_shapely.is_valid:
                continue
        polygons_shapely.append(polygon_shapely)
    return polygons_shapely


def is_fully_within_analysis_boundary(polygon, analysis_area_bbox):
    t = 0.00002 # threshold in degrees
    pminx, pminy, pmaxx, pmaxy = polygon.bounds
    aaminx, aaminy, aamaxx, aamaxy = analysis_area_bbox.bounds
    return abs(pminx-aaminx)>t and abs(pminy-aaminy)>t and abs(pmaxx-aamaxx)>t and abs(pmaxy-aamaxy)>t


def to_geojson(polys_shapely, analysis_area_bbox, longitude, latitude):
    # Break out early and return empty geometry collection
    # if no polygons were found.
    if not polys_shapely:
        return '{"type": "FeatureCollection", "features": []}'
    # Process polygons
    geod = Geod(ellps="WGS84")
    records = []
    for poly in polys_shapely:
        # Calculate perimeter and area
        poly_area, poly_perimeter = geod.geometry_area_perimeter(poly)
        records.append({
            'perimeter': int(poly_perimeter),
            'area': int(abs(poly_area)),
            'fully_within_analysis_boundary': is_fully_within_analysis_boundary(poly, analysis_area_bbox),
            'geometry': poly
        })
    # Turn analysis centerpoint into geometry for nearest distance join
    gdf_centerpoint = gpd.GeoDataFrame({'geometry':[Point(longitude, latitude)]}, geometry='geometry', crs='epsg:4326').to_crs('epsg:3857')
    # Create geopandas dataframe from footprints
    gdf = gpd.GeoDataFrame(pd.DataFrame.from_records(records), geometry='geometry', crs='epsg:4326').to_crs('epsg:3857')
    gdf = gdf.sjoin_nearest(gdf_centerpoint, how='left', distance_col='proximity').drop(columns='index_right')
    gdf['proximity'] = gdf['proximity'].astype(int)
    gdf['rank_proximity'] = gdf['proximity'].rank(method='min').astype(int)
    gdf = gdf.to_crs('epsg:4326')
    return gdf.to_json(drop_id=True)
