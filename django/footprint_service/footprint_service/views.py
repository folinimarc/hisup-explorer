from django.views import View
from footprint_service.models import Footprint
from rest_framework import viewsets
from footprint_service.serializers import FootprintSerializer
from footprint_service.tasks import process_item
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from django.conf import settings


class FootprintViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = Footprint.objects.all().order_by("-created")
    serializer_class = FootprintSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fobj = serializer.save()

        # Hand off to celery
        process_item.delay(fobj.pk)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ExplorerView(View):

    def get(self, request):
        ctx = {
            'bing_key': settings.BING_KEY
        }
        return render(request, 'footprint_service/explorer.html', ctx)
