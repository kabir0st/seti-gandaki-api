from core.utils.viewsets import DefaultViewSet

from ..models.logistics import GatePass
from ..serializers import GatePassSerializer
from .filtersets import GatePassFilterSet


class GatePassViewSet(DefaultViewSet):
    """
    API endpoint that allows gate passes to be viewed or edited.
    """
    queryset = GatePass.objects.all().select_related(
        'vehicle', 'issued_by').order_by('-entry_time')
    serializer_class = GatePassSerializer
    filterset_class = GatePassFilterSet
    search_fields = [
        'vehicle__license_plate',
        'license_plate',
        'purpose',
        'driver_name',
        'driver_phone',
        'issued_by__username',
        'issued_by__first_name',
        'issued_by__last_name',
        'remarks',
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
