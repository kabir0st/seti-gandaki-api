from rest_framework import permissions
from core.utils.viewsets import DefaultViewSet
from ..serializers import VehicleSerializer
from ..models.logistics import Vehicle  # Added explicit import
# from .filtersets.vehicle import VehicleFilterSet  # Placeholder


class VehicleViewSet(DefaultViewSet):
    """
    API endpoint that allows vehicles to be viewed or edited.
    """
    queryset = Vehicle.objects.all().order_by('-created_at')
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]  # Adjust as needed
    # filterset_class = VehicleFilterSet # Placeholder
    search_fields = [
        'license_plate',
        # 'model', # Removed
        # 'type', # Removed
        # 'business__name' # Removed, business FK is no longer on Vehicle
    ]
    ordering_fields = [
        'license_plate',
        # 'model', # Removed
        # 'type', # Removed
        'created_at',
        'updated_at',
        # 'business__name' # Removed
    ]
