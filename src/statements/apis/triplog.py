from rest_framework import permissions
from core.utils.viewsets import DefaultViewSet
from ..models.logistics import TripLog
from ..serializers import TripLogSerializer
# from .filtersets.triplog import TripLogFilterSet # Placeholder


class TripLogViewSet(DefaultViewSet):
    """
    API endpoint that allows trip logs to be viewed or edited.
    """
    queryset = TripLog.objects.all().select_related(
        'vehicle', 'for_purchase_bill').order_by(
            '-created_at')  # Updated related fields and ordering
    serializer_class = TripLogSerializer
    permission_classes = [permissions.IsAuthenticated]  # Adjust as needed
    # filterset_class = TripLogFilterSet # Placeholder
    search_fields = [
        'vehicle__license_plate',
        # 'start_location', # Removed
        # 'end_location', # Removed
        # 'driver__username', # Removed
        # 'driver__first_name', # Removed
        # 'driver__last_name', # Removed
        # 'driver_name_text', # Removed
        'purpose',
        'notes',  # Added
        # 'gate_pass__id' # Removed
        'for_purchase_bill__purchase_bill_number',  # Added
    ]
    ordering_fields = [
        # 'start_time', # Removed
        # 'end_time', # Removed
        'vehicle__license_plate',
        # 'start_location', # Removed
        # 'end_location', # Removed
        # 'driver__username', # Removed
        'created_at',
        'updated_at',
        'for_purchase_bill__purchase_bill_number',  # Added
    ]
