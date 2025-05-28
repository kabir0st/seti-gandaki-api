from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from core.utils.viewsets import DefaultViewSet
from ..serializers import VehicleSerializer
from ..models.purchase_invoice import Vehicle
from .filtersets import VehicleFilterSet


class VehicleViewSet(DefaultViewSet):
    queryset = Vehicle.objects.all().order_by('-created_at')
    serializer_class = VehicleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = VehicleFilterSet
    search_fields = [
        'license_plate',
        'vehicle_type',
    ]
