import django_filters
from hrm.models.salary import SalaryDisbursement


class SalaryDisbursementFilter(django_filters.FilterSet):
    staff = django_filters.CharFilter(field_name='staff__name', lookup_expr='icontains', label='Staff Name')
    from_date = django_filters.DateFilter(field_name='from_date', lookup_expr='gte', label='From Date (YYYY-MM-DD)')
    to_date = django_filters.DateFilter(field_name='to_date', lookup_expr='lte', label='To Date (YYYY-MM-DD)')
    month = django_filters.NumberFilter(field_name='from_date__month', label='Month (1-12)')
    year = django_filters.NumberFilter(field_name='from_date__year', label='Year (YYYY)')
    min_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='gte', label='Min Amount')
    max_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='lte', label='Max Amount')
    created_by = django_filters.CharFilter(field_name='created_by__username', lookup_expr='icontains', label='Created By (Username)')
    created_at_after = django_filters.DateFilter(field_name='created_at__date', lookup_expr='gte', label='Created After (YYYY-MM-DD)')
    created_at_before = django_filters.DateFilter(field_name='created_at__date', lookup_expr='lte', label='Created Before (YYYY-MM-DD)')

    class Meta:
        model = SalaryDisbursement
        fields = [
            'staff', 'from_date', 'to_date', 'month', 'year',
            'min_amount', 'max_amount', 'created_by',
            'created_at_after', 'created_at_before'
        ]