import django_filters
from hrm.models.salary import SalaryDisbursement


class SalaryDisbursementFilter(django_filters.FilterSet):
    staff = django_filters.CharFilter(field_name='staff__name', lookup_expr='icontains')
    from_date = django_filters.DateFilter(field_name='from_date', lookup_expr='gte')
    to_date = django_filters.DateFilter(field_name='to_date', lookup_expr='lte')
    month = django_filters.NumberFilter(field_name='from_date__month', label='Month (1-12)')
    year = django_filters.NumberFilter(field_name='from_date__year', label='Year (YYYY)')


    class Meta:
        model = SalaryDisbursement
        fields = ['staff', 'from_date', 'to_date', 'month', 'year']