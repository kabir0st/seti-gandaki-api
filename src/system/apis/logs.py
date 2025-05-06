from auditlog.models import LogEntry
from core.utils.permissions import IsStaff
from core.utils.viewsets import DefaultViewSet
from system.apis.filtersets.misc import AuditLogFilterSet, AuthLogSet
from system.models import AuthenticationLog
from system.serializers.logs import AuthLogSerializer, LogEntrySerializer


class AuthLogAPI(DefaultViewSet):
    queryset = AuthenticationLog.objects.filter().order_by('-id')
    http_method_names = ['get']
    serializer_class = AuthLogSerializer
    search_fields = ["user__given_name", 'user__family_name', 'user__email']
    filterset_class = AuthLogSet
    permission_classes = [IsStaff]


class AuditLogAPI(DefaultViewSet):
    queryset = LogEntry.objects.filter().order_by('-id')
    http_method_names = ['get']
    serializer_class = LogEntrySerializer
    search_fields = ["actor__given_name", 'actor__family_name', 'actor__email']
    filterset_class = AuditLogFilterSet
    permission_classes = [IsStaff]
