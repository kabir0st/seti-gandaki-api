import django_filters
from statements.models.logistics import TripLog


class TripLogFilterSet(django_filters.FilterSet):
    vehicle_license_plate = django_filters.CharFilter(
        field_name='vehicle__license_plate', lookup_expr='iexact')
    vehicle_license_plate__icontains = django_filters.CharFilter(
        field_name='vehicle__license_plate', lookup_expr='icontains')
    purchase_bill_number = django_filters.CharFilter(
        field_name='for_purchase_bill__purchase_bill_number',
        lookup_expr='iexact')
    purchase_bill_number__icontains = django_filters.CharFilter(
        field_name='for_purchase_bill__purchase_bill_number',
        lookup_expr='icontains')
    purpose__icontains = django_filters.CharFilter(field_name='purpose',
                                                   lookup_expr='icontains')
    created_at_after = django_filters.DateTimeFilter(field_name='created_at',
                                                     lookup_expr='gte')
    created_at_before = django_filters.DateTimeFilter(field_name='created_at',
                                                      lookup_expr='lte')

    class Meta:
        model = TripLog
        fields = [
            'vehicle',
            'for_purchase_bill',
            'vehicle_license_plate',
            'vehicle_license_plate__icontains',
            'purchase_bill_number',
            'purchase_bill_number__icontains',
            'purpose__icontains',
            'created_at_after',
            'created_at_before',
        ]
