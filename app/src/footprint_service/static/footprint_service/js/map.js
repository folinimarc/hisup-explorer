'use strict';


class LeafletWrapper {
  constructor(conf) {
    this.domElementId = conf['domElementId'] || 'map';
    this.domElement = document.getElementById( this.domElementId)
    this.initViewCenterlatLng = conf['initViewCenterlatLng']  || [47.34, 8.45];
    this.initZoomLevel = conf['zoomLevel'] || 6;

    this.layer_basemap_osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 18, attribution: '© OpenStreetMap'});
    this.layer_basemap_bing = L.tileLayer.bing("AoKXEIq7_Yw2gVJgbptkOEm9iKgQBSJ7UY2pswBckCh37x4nja-TNED-dHhdIPN7", {'imagerySet': 'Aerial'});

    this.map = L.map(this.domElement, {
      center: this.initViewCenterlatLng,
      zoom: this.initZoomLevel,
      layers: [this.layer_basemap_osm, this.layer_basemap_bing]
    })

    this.layerControl = L.control.layers({
      'OpenStreetMap': this.layer_basemap_osm,
      'Bing Satellite': this.layer_basemap_bing
    }, null, {position: 'topleft'}).addTo(this.map)

    this.layer_footprints = L.geoJSON(null);
    this.layer_analysisarea = L.geoJSON(null, {
      style: {
        weight: 2,
        fillOpacity: 0,
        color: 'white',
        dashArray: '7, 7',
        dashOffset: '0'
      }
    });
  }

  visualizeFootprints(bbox_analysis_geojson, footprints_geojson) {

    // clear any existing features
    this.layer_analysisarea.clearLayers();
    this.layer_footprints.clearLayers();

    // update analysis area
    this.layer_analysisarea.addData(bbox_analysis_geojson).addTo(this.map);

    // Update footprints layer, set style and popups
    this.layer_footprints.addData(footprints_geojson).addTo(this.map);
    this.layer_footprints.eachLayer((layer) => {
      // bind popup
      let props = layer.feature.properties
      let popup = `Rank proximity: ${props.rank_proximity}<br/>Proximity: ${props.proximity}<br/>Area: ${props.area}<br/>Fully contained: ${props.fully_within_analysis_boundary}`
      layer.bindPopup(popup);
      // set style (random colors)
      layer.setStyle({
        color: '#'+(0x1000000+(Math.random())*0xffffff).toString(16).substr(1,6),
        fillOpacity: 0.3
      })
    })

    // zoom to new footprints. Add small negative padding to avoid
    // that it always zooms to next larger zoom level.
    this.map.fitBounds(this.layer_analysisarea.getBounds().pad(-0.05));

  }

  getCenterlatLngZoom() {
    let latLng = this.map.getBounds().getCenter()
    return {
      latitude: latLng['lat'],
      longitude: latLng['lng'],
      zoom : this.map.getZoom()
    }
  }

}
