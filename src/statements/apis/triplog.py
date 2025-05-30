from rest_framework import permissions
from core.utils.viewsets import DefaultViewSet
from ..models.logistics import TripLog
from ..serializers import TripLogSerializer
from .filtersets import TripLogFilterSet


class TripLogViewSet(DefaultViewSet):
    """
    API endpoint that allows trip logs to be viewed or edited.
    """
    queryset = TripLog.objects.all().select_related(
        'gate_pass', 'for_purchase_bill', 'for_invoice').order_by('-created_at')
    serializer_class = TripLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = TripLogFilterSet
    search_fields = [
        'gate_pass__vehicle__license_plate',
        'purpose',
        'notes',
        'for_purchase_bill__purchase_bill_number',
    ]
