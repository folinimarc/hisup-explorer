from django.contrib import admin
from footprint_service.models import Footprint
from django.utils.html import mark_safe
from django.conf import settings
from django.shortcuts import get_object_or_404


class FootprintAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status',)
    readonly_fields=['id', 'longitude', 'latitude', 'zoom_level','status', 'error_traceback', 'created', 'started', 'finished', 'is_valid_img', 'bbox_analysis_geojson', 'footprints_geojson']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['obj'] = get_object_or_404(Footprint, pk=object_id)
        extra_context['bing_key'] = settings.BING_KEY
        return super(FootprintAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

admin.site.register(Footprint, FootprintAdmin)
