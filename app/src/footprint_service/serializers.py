from footprint_service.models import Footprint
from rest_framework import serializers
import json


class FootprintSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Footprint
        fields = ['id', 'latitude', 'longitude', 'zoom_level', 'status', 'error_traceback', 'created', 'started', 'finished', 'is_valid_img', 'bbox_analysis_geojson', 'footprints_geojson']
        read_only_fields = ['id', 'status', 'error_traceback', 'created', 'started', 'finished', 'is_valid_img', 'bbox_analysis_geojson', 'footprints_geojson']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['bbox_analysis_geojson'] = json.loads(rep['bbox_analysis_geojson']) if rep['bbox_analysis_geojson'] else None
        rep['footprints_geojson'] = json.loads(rep['footprints_geojson']) if rep['bbox_analysis_geojson'] else None
        return rep
