from rest_framework import serializers
from .models.purchase_invoice import PurchaseBill, PurchaseItem
from .models.business import Business
from .models.logistics import Vehicle, GatePass, GatePassMovement, TripLog


# Serializer for Business model
class BusinessSerializer(serializers.ModelSerializer):

    class Meta:
        model = Business
        fields = '__all__'


class VehicleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vehicle
        fields = [
            'id', 'license_plate', 'primary_staffs', 'image', 'vehicle_type',
            'note', 'is_active', 'created_at', 'updated_at'
        ]


class GatePassMovementSerializer(serializers.ModelSerializer):

    class Meta:
        model = GatePassMovement
        fields = [
            'id', 'gate_pass', 'exit_time', 'entry_time', 'created_at',
            'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')


class GatePassSerializer(serializers.ModelSerializer):
    vehicle_details = VehicleSerializer(source='vehicle',
                                        read_only=True,
                                        allow_null=True)
    movements = GatePassMovementSerializer(many=True, read_only=True)

    class Meta:
        model = GatePass
        fields = [
            'id', 'vehicle', 'vehicle_details', 'license_plate', 'purpose',
            'driver_name', 'driver_phone', 'remarks', 'issued_by',
            'created_at', 'updated_at', 'movements'
        ]
        extra_kwargs = {
            'vehicle': {
                'allow_null': True,
                'required': False
            },
            'issued_by': {
                'allow_null': True,
                'required': False
            },
        }


class TripLogSerializer(serializers.ModelSerializer):
    gate_pass_details = VehicleSerializer(source='gate_pass', read_only=True)

    class Meta:
        model = TripLog
        fields = [
            'id', 'gate_pass', 'gate_pass_details', 'for_purchase_bill',
            'purpose', 'notes', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'for_purchase_bill': {
                'allow_null': True,
                'required': False
            },
        }


class PurchaseItemBaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = PurchaseItem
        fields = '__all__'
        read_only_fields = (
            'sub_total',
            'taxable_amount',
            'tax_amount',
            'bill_amount',
        )


class PurchaseItemListSerializer(serializers.ModelSerializer):

    class Meta:
        model = PurchaseItem
        fields = (
            'id',
            'purchase_bill',
            'item',
            'item_description',
            'quantity',
            'unit_of_measurement',
            'unit_price',
            'discount_percentage',
            'tax_percent_applied',
            'bill_amount',
            'created_at',
        )


class PurchaseItemDetailSerializer(PurchaseItemBaseSerializer):
    pass


# Serializer for PurchaseBill
class PurchaseBillSerializer(serializers.ModelSerializer):
    purchase_items = PurchaseItemBaseSerializer(many=True, read_only=True)

    # For displaying 'from_business' details on GET
    from_business_details = BusinessSerializer(source='from_business',
                                               read_only=True,
                                               allow_null=True)

    # For writing 'from_business' Foreign Key on POST/PUT
    # This field allows setting the FK by providing the ID of the Business.
    # 'source' links this serializer field to the 'from_business' model field.
    from_business = serializers.PrimaryKeyRelatedField(
        queryset=Business.objects.all(),
        allow_null=True,
        required=False,
        # write_only=True # Make it write_only if you ONLY want
        # from_business_details for read.
        # If not write_only, 'from_business' will appear as ID on read
        # if from_business_details is not used.
        # For clarity, often one is write_only and the other read_only
        # with a different name.
        # Let's adjust: make this the primary way to interact,
        # and details is just for output.
    )

    class Meta:
        model = PurchaseBill
        fields = (
            'id',
            'purchase_date',
            'from_business',  # Writable FK (ID), also readable as ID
            'from_business_details',  # Read-only nested representation
            'purchase_bill_number',
            'sub_total',  # Read-only (calculated via PurchaseItem signals)
            'grace_discount',
            'shipping_and_handling_costs',
            'additional_costs',
            'additional_costs_remarks',
            'bill_amount',  # Read-only (calculated via PurchaseItem signals)
            'paid_amount',
            'shipping_handling_receipt',
            'status',
            'purchase_receipt',
            'notes',
            'created_at',
            'updated_at',
            'purchase_items'  # Read-only nested items
        )
        read_only_fields = (
            'sub_total',
            'bill_amount',
        )
