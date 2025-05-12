import django_filters
from statements.models.purchase_invoice import Vehicle


class VehicleFilterSet(django_filters.FilterSet):
    license_plate = django_filters.CharFilter(lookup_expr='iexact')
    license_plate__icontains = django_filters.CharFilter(
        field_name='license_plate', lookup_expr='icontains')
    vehicle_type = django_filters.CharFilter(lookup_expr='iexact')
    vehicle_type__icontains = django_filters.CharFilter(
        field_name='vehicle_type', lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Vehicle
        fields = ['license_plate', 'vehicle_type', 'is_active']
