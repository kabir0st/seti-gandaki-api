from auditlog.models import LogEntry
from django.contrib.auth.models import Group, Permission
from django_filters import DateTimeFromToRangeFilter, FilterSet

from core.utils.viewsets import (DefaultFilterSet, ExcludeFilterSet,
                                 UserIncludedFilterSet)
from system.models.log import AuthenticationLog
from system.models.misc import Document
from system.models.notification import Notification


class DocumentFilterSet(DefaultFilterSet):

    class Meta:
        model = Document
        exclude = ('document', )


class AuthLogSet(DefaultFilterSet, UserIncludedFilterSet):

    class Meta:
        model = AuthenticationLog
        exclude = ('document', )


class AuditLogFilterSet(FilterSet):
    timestamp = DateTimeFromToRangeFilter(field_name='timestamp')

    class Meta:
        model = LogEntry
        exclude = ('serialized_data', 'changes', 'additional_data')


class NotificationFilterSet(DefaultFilterSet):

    class Meta:
        model = Notification
        fields = "__all__"


class PermissionFilterSet(ExcludeFilterSet):

    class Meta:
        model = Permission
        fields = "__all__"


class GroupFilterSet(ExcludeFilterSet):

    class Meta:
        model = Group
        fields = "__all__"
