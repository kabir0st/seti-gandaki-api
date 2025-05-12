import django_filters
from statements.models.logistics import GatePass
from django.contrib.auth import get_user_model

User = get_user_model()


class GatePassFilterSet(django_filters.FilterSet):
    vehicle_license_plate = django_filters.CharFilter(
        field_name='vehicle__license_plate', lookup_expr='iexact')
    vehicle_license_plate__icontains = django_filters.CharFilter(
        field_name='vehicle__license_plate', lookup_expr='icontains')
    license_plate = django_filters.CharFilter(lookup_expr='iexact')
    license_plate__icontains = django_filters.CharFilter(
        field_name='license_plate', lookup_expr='icontains')
    driver_name__icontains = django_filters.CharFilter(
        field_name='driver_name', lookup_expr='icontains')
    driver_phone = django_filters.CharFilter(field_name='driver_phone',
                                             lookup_expr='iexact')
    entry_time_after = django_filters.DateTimeFilter(field_name='entry_time',
                                                     lookup_expr='gte')
    entry_time_before = django_filters.DateTimeFilter(field_name='entry_time',
                                                      lookup_expr='lte')
    exit_time_after = django_filters.DateTimeFilter(field_name='exit_time',
                                                    lookup_expr='gte')
    exit_time_before = django_filters.DateTimeFilter(field_name='exit_time',
                                                     lookup_expr='lte')
    is_open = django_filters.BooleanFilter(field_name='exit_time',
                                           lookup_expr='isnull')
    issued_by_username = django_filters.ModelChoiceFilter(
        field_name='issued_by__username',
        to_field_name='username',
        queryset=User.objects.all(),
        lookup_expr='iexact')

    class Meta:
        model = GatePass
        fields = [
            'vehicle_license_plate',
            'license_plate',
            'driver_name__icontains',
            'driver_phone',
            'entry_time_after',
            'entry_time_before',
            'exit_time_after',
            'exit_time_before',
            'is_open',
            'issued_by_username',
        ]
