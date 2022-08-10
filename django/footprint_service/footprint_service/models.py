from django.db import models
from django.utils.html import escape

class Footprint(models.Model):
    status = models.CharField(max_length=20, default='PENDING')
    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(null=True, blank=True)
    finished = models.DateTimeField(null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    zoom_level = models.IntegerField(default=18, blank=True)
    bbox_analysis_geojson = models.TextField(null=True, blank=True)
    footprints_geojson = models.TextField(null=True, blank=True)
    is_valid_img = models.BooleanField(null=True, blank=True)
    error_traceback = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'Footprint {self.pk} ({self.status})'
