from django.core.validators import RegexValidator
from rest_framework import serializers
from hrm.models.fuel import FuelTicket, PetrolStation
from system.serializers.users import MiniUserBaseSerializer

class PetrolStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetrolStation
        fields = (
            'id', 'name', 'station_code', 'location_details', 
            'is_active', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

class FuelTicketSerializer(serializers.ModelSerializer):
    dispatched_by = MiniUserBaseSerializer(read_only=True)
    
    consumed_by_station = PetrolStationSerializer(read_only=True)
    consumed_by_station_id = serializers.PrimaryKeyRelatedField(
        queryset=PetrolStation.objects.filter(is_active=True),
        source='consumed_by_station',
        write_only=True,
        allow_null=True,
        required=False
    )
    ticket_url = serializers.SerializerMethodField()

    class Meta:
        model = FuelTicket
        fields = (
            'id', 'ticket_id', 'dispatched_by',  'fuel_type', 'quantity_liters',
            'vehicle_registration_number', 'driver_name', 'driver_phone', 'remarks',
            'is_consumed', 'consumed_at', 'consumed_by_station', 'consumed_by_station_id',
            'created_at', 'updated_at', 'ticket_url'
        )
        read_only_fields = (
            'id', 'ticket_id', 'is_consumed', 'consumed_at', 
            'created_at', 'updated_at', 'ticket_url'
        )

    def get_ticket_url(self, obj):
        return f"/verify-fuel-ticket/{obj.ticket_id}/" 

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if instance.is_consumed and not self.context['request'].user.is_staff:
             raise serializers.ValidationError("Consumed tickets cannot be modified by non-staff.")
        return super().update(instance, validated_data)


class FuelTicketConsumeSerializer(serializers.Serializer):
    station_code = serializers.CharField(
        max_length=4,
        validators=[RegexValidator(r'^\d{4}$', 'Station code must be 4 digits.')]
    )

    def validate_station_code(self, value):
        try:
            station = PetrolStation.objects.get(station_code=value, is_active=True)
            self.context['station'] = station 
        except PetrolStation.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive station code.")
        return value

    def save(self, **kwargs):
        ticket = self.context['ticket'] 
        station = self.context['station']
        
        if ticket.is_consumed:
            raise serializers.ValidationError(f"Ticket already consumed at {ticket.consumed_by_station.name} on {ticket.consumed_at.strftime('%Y-%m-%d %H:%M')}.")

        ticket.mark_as_consumed(station=station)
        return ticket

class FuelTicketPublicDetailSerializer(serializers.ModelSerializer):
    dispatched_by = MiniUserBaseSerializer(read_only=True)
    fuel_type = serializers.CharField(source='get_fuel_type_display', read_only=True)

    class Meta:
        model = FuelTicket
        fields = (
            'ticket_id', 'fuel_type', 'quantity_liters', 
            'vehicle_registration_number', 'driver_name',
            'dispatched_by', 'created_at', 'is_consumed'
        )
        read_only_fields = fields