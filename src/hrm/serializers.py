from decimal import Decimal
from django.core.validators import RegexValidator, MinValueValidator
from rest_framework import serializers
from hrm.models.fuel import FuelTicket, PetrolStation
from hrm.models.attendance import Attendance, AttendanceChoice
from statements.serializers import StaffSerializer # Import StaffSerializer
from hrm.models.salary import SalaryDisbursement
from system.serializers.users import MiniUserBaseSerializer
from hrm.models.food_ticket import FoodTicket

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
        validators=[RegexValidator(r'^\d{4}$', 'Station code must be 4 digits.')],
        required=True
    )
    bill_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        required=True
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
        validated_data = self.validated_data # Access validated_data here
        
        if ticket.is_consumed:
            raise serializers.ValidationError(f"Ticket already consumed at {ticket.consumed_by_station.name} on {ticket.consumed_at.strftime('%Y-%m-%d %H:%M')}.")

        # Set the bill_amount on the ticket instance from validated data
        ticket.bill_amount = validated_data.get('bill_amount')
        
        # Pass bill_amount to mark_as_consumed if that method is adapted to take it,
        # or ensure mark_as_consumed saves it if it's part of update_fields.
        # For now, bill_amount is set on the instance, mark_as_consumed will save it if included in update_fields.
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


class AttendanceSerializer(serializers.ModelSerializer):
    staff = StaffSerializer(read_only=True)
    staff_id = serializers.PrimaryKeyRelatedField(
        queryset=StaffSerializer.Meta.model.objects.all(), # Use Staff model from StaffSerializer
        source='staff',
        write_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Attendance
        fields = (
            'id', 'staff', 'staff_id', 'date', 'check_in_time', 'check_out_time',
            'status', 'status_display', 'remarks', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'status_display')

    def validate(self, data):
        staff = data.get('staff')
        date = data.get('date')

        # For POST (create)
        if not self.instance:
            if Attendance.objects.filter(staff=staff, date=date).exists():
                raise serializers.ValidationError(
                    {"detail": f"Attendance for {staff.name} on {date} already exists."}
                )
        # For PUT/PATCH (update)
        else:
            if Attendance.objects.filter(staff=staff, date=date).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError(
                    {"detail": f"Attendance for {staff.name} on {date} already exists."}
                )
        return data
class SalaryDisbursementSerializer(serializers.ModelSerializer):
    staff = StaffSerializer(read_only=True)
    staff_id = serializers.PrimaryKeyRelatedField(
        queryset=StaffSerializer.Meta.model.objects.all(),
        source='staff',
        write_only=True
    )
    created_by = MiniUserBaseSerializer(read_only=True)

    class Meta:
        model = SalaryDisbursement
        fields = (
            'id', 'staff', 'staff_id', 'from_date', 'to_date', 'amount',
            'remarks', 'created_by', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
class FoodTicketSerializer(serializers.ModelSerializer):
    staff = StaffSerializer(read_only=True)
    staff_id = serializers.PrimaryKeyRelatedField(
        queryset=StaffSerializer.Meta.model.objects.all(),
        source='staff',
        write_only=True,
        help_text="ID of the staff member receiving the ticket."
    )
    issued_by = MiniUserBaseSerializer(read_only=True)
    meal_type_display = serializers.CharField(source='get_meal_type_display', read_only=True)

    class Meta:
        model = FoodTicket
        fields = (
            'id', 'staff', 'staff_id', 'issued_by', 'ticket_number', 
            'meal_type', 'meal_type_display', 'issued_at', 'is_used', 
            'used_at', 'notes', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'issued_by', 'ticket_number', 'issued_at', 
            'created_at', 'updated_at', 'meal_type_display'
        )

    def create(self, validated_data):
        validated_data['issued_by'] = self.context['request'].user
        # Ticket number is auto-generated by model's save method
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Potentially add logic here if certain fields cannot be updated after creation
        # or based on ticket status (e.g., if already used)
        if instance.is_used and not self.context['request'].user.is_staff:
             raise serializers.ValidationError("Used tickets cannot be modified by non-staff users.")
        return super().update(instance, validated_data)

class FoodTicketMarkAsUsedSerializer(serializers.Serializer):
    """
    Serializer for marking a food ticket as used.
    No input fields needed as the ticket ID comes from the URL.
    """
    def update(self, instance, validated_data):
        if instance.is_used:
            raise serializers.ValidationError(f"Ticket {instance.ticket_number} was already used at {instance.used_at.strftime('%Y-%m-%d %H:%M')}.")
        
        from django.utils import timezone
        instance.is_used = True
        instance.used_at = timezone.now()
        instance.save(update_fields=['is_used', 'used_at'])
        return instance