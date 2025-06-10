from core.utils.permissions import IsAuthenticated
from core.utils.viewsets import DefaultViewSet
from statements.apis.filtersets.business_credit_log import BusinessCreditLogFilterSet
from statements.models.business_credit_log import BusinessCreditLog
from statements.serializers import BusinessCreditLogSerializer


class BusinessCreditLogAPI(DefaultViewSet):
    queryset = BusinessCreditLog.objects.all().order_by('-created_at')
    serializer_class = BusinessCreditLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = BusinessCreditLogFilterSet
    http_method_names = ["get", "post", "patch", "delete"]
    search_fields = ["business__name", "remarks"]