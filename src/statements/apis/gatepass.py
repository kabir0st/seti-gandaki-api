from rest_framework import permissions
from core.utils.viewsets import DefaultViewSet
from ..models.logistics import GatePass
from ..serializers import GatePassSerializer
# from .filtersets.gatepass import GatePassFilterSet # Placeholder


class GatePassViewSet(DefaultViewSet):
    """
    API endpoint that allows gate passes to be viewed or edited.
    """
    queryset = GatePass.objects.all().select_related(
        'vehicle', 'issued_by').order_by('-entry_time')  # Removed 'business'
    serializer_class = GatePassSerializer
    permission_classes = [permissions.IsAuthenticated]  # Adjust as needed
    # filterset_class = GatePassFilterSet # Placeholder
    search_fields = [
        'vehicle__license_plate',
        'license_plate',  # Added direct license_plate search on GatePass
        # 'business__name', # Removed
        'purpose',
        # 'destination', # Removed from GatePass model
        'driver_name',
        'driver_phone',
        'issued_by__username',
        'issued_by__first_name',
        'issued_by__last_name',
        'remarks',  # Added remarks
    ]
    ordering_fields = [
        'entry_time',
        'exit_time',
        'vehicle__license_plate',
        'license_plate',  # Added
        # 'business__name', # Removed
        'created_at',
        'updated_at',
    ]
