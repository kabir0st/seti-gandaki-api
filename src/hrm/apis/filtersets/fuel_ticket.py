import django_filters
from django.conf import settings

from hrm.models.fuel import PetrolStation, FuelTicket
from statements.models.purchase_invoice import Vehicle # For FuelTicket.vehicle filter

class PetrolStationFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    station_code = django_filters.CharFilter(lookup_expr='exact')
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = PetrolStation
        fields = ['name', 'station_code', 'is_active']

class FuelTicketFilter(django_filters.FilterSet):
    ticket_id = django_filters.UUIDFilter(field_name='ticket_id', lookup_expr='exact')
    dispatched_by = django_filters.ModelChoiceFilter(
        field_name='dispatched_by',
        queryset=settings.AUTH_USER_MODEL.objects.all(), # This might need adjustment if AUTH_USER_MODEL is not directly queryable here
        to_field_name='id' # Assuming filtering by user ID
    )
    fuel_type = django_filters.ChoiceFilter(choices=FuelTicket.FuelType.choices)
    vehicle_registration_number = django_filters.CharFilter(lookup_expr='icontains')
    vehicle = django_filters.ModelChoiceFilter(
        queryset=Vehicle.objects.all(),
        to_field_name='id' # Assuming filtering by Vehicle ID
    )
    is_consumed = django_filters.BooleanFilter()
    consumed_by_station = django_filters.ModelChoiceFilter(
        queryset=PetrolStation.objects.all(),
        to_field_name='id' # Assuming filtering by PetrolStation ID
    )
    created_at = django_filters.DateFromToRangeFilter()
    consumed_at = django_filters.DateFromToRangeFilter()


    class Meta:
        model = FuelTicket
        fields = [
            'ticket_id',
            'dispatched_by',
            'fuel_type',
            'vehicle_registration_number',
            'vehicle',
            'is_consumed',
            'consumed_by_station',
            'created_at',
            'consumed_at',
        ]