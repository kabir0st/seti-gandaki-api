import django_filters
from statements.models.support import Staff


class StaffFilterSet(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    phone_number = django_filters.CharFilter(lookup_expr='icontains')
    pan = django_filters.CharFilter(lookup_expr='iexact')
    pan__icontains = django_filters.CharFilter(field_name='pan',
                                               lookup_expr='icontains')

    class Meta:
        model = Staff
        fields = ['name', 'phone_number', 'pan']
