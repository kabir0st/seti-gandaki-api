from django_filters import DateFromToRangeFilter, CharFilter

from core.utils.viewsets import ExcludeFilterSet
from statements.models.business_credit_log import BusinessCreditLog


class BusinessCreditLogFilterSet(ExcludeFilterSet):
    created_at = DateFromToRangeFilter(field_name='created_at')
    updated_at = DateFromToRangeFilter(field_name='updated_at')
    action = CharFilter(field_name='action', lookup_expr='iexact')

    class Meta:
        model = BusinessCreditLog
        exclude = ('receipt',)