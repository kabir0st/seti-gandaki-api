from rest_framework import serializers
from .models.purchase_invoice import PurchaseBill, PurchaseItem
from .models.business import Business
from .models.logistics import Vehicle, GatePass, TripLog


# Serializer for Business model
class BusinessSerializer(serializers.ModelSerializer):

    class Meta:
        model = Business
        fields = '__all__'  # Include all fields from the Business model


class VehicleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vehicle
        fields = [
            'id', 'license_plate', 'is_active', 'created_at', 'updated_at'
        ]  # Removed 'business', 'model', 'type'


class GatePassSerializer(serializers.ModelSerializer):
    vehicle_details = VehicleSerializer(source='vehicle',
                                        read_only=True,
                                        allow_null=True)  # vehicle can be null

    # 'business' field removed from GatePass model, so no business_details

    # issued_by_details can be added if a UserSerializer is available
    # issued_by_details = UserSerializer(
    #    source='issued_by', read_only=True, allow_null=True
    # )

    class Meta:
        model = GatePass
        fields = [
            'id',
            'vehicle',
            'vehicle_details',
            'license_plate',
            'entry_time',
            'exit_time',
            'purpose',
            'driver_name',
            'driver_phone',
            'remarks',
            'issued_by',  # 'issued_by_details', # Add if using UserSerializer
            'created_at',
            'updated_at'
        ]  # Removed 'business'
        extra_kwargs = {
            'vehicle': {
                'allow_null': True,
                'required': False
            },  # vehicle can be null
            # 'business' related extra_kwargs removed
            'issued_by': {
                'allow_null': True,
                'required': False
            },
        }


class TripLogSerializer(serializers.ModelSerializer):
    vehicle_details = VehicleSerializer(source='vehicle', read_only=True)

    # 'gate_pass' field removed from TripLog model.
    # 'driver' and 'driver_name_text' fields removed.

    # Optional: For displaying purchase bill details on GET
    # purchase_bill_details = PurchaseBillSerializer(
    #     source='for_purchase_bill', read_only=True, allow_null=True
    # )

    class Meta:
        model = TripLog
        fields = [
            'id',
            'vehicle',
            'vehicle_details',
            'for_purchase_bill',
            # 'purchase_bill_details', # Add if using PurchaseBillSerializer
            'purpose',
            'notes',
            'created_at',
            'updated_at'
        ]
        # 'duration_hours', 'distance_km' removed.
        extra_kwargs = {
            'vehicle': {
                'write_only': False
            },  # vehicle is mandatory
            'for_purchase_bill': {
                'allow_null': True,
                'required': False
            },
            # 'gate_pass' and 'driver' related extra_kwargs removed
        }


# Base serializer for PurchaseItem, includes all fields and read-only
# calculated fields
class PurchaseItemBaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = PurchaseItem
        fields = '__all__'
        read_only_fields = (
            'sub_total',
            'taxable_amount',
            'tax_amount',
            'bill_amount',  # Final bill_amount of item, calculated by signal
        )


# Serializer for PurchaseItem list view
class PurchaseItemListSerializer(serializers.ModelSerializer):
    # Example: To show purchase_bill_number directly in the list
    # purchase_bill_number = serializers.CharField(
    #     source='purchase_bill.purchase_bill_number', read_only=True
    # )

    class Meta:
        model = PurchaseItem
        fields = (
            'id',
            'purchase_bill',  # Foreign Key to PurchaseBill (resolves to ID)
            'item',
            'item_description',
            'quantity',
            'unit_of_measurement',
            'unit_price',
            'discount_percentage',
            'tax_percent_applied',
            'bill_amount',  # Final bill_amount of the item
            'created_at',
        )


# Serializer for PurchaseItem detail view (create, update, retrieve)
class PurchaseItemDetailSerializer(PurchaseItemBaseSerializer):
    # Inherits all fields and read_only_fields from PurchaseItemBaseSerializer
    # If you need to represent 'purchase_bill' with more detail on read:
    # purchase_bill = PurchaseBillLightSerializer(read_only=True)
    # # Define PurchaseBillLightSerializer separately
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

    # If you want 'from_business' to be write_only and
    # 'from_business_details' to be the sole representation for
    # reading 'from_business':
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if self.context.get('request') and \
    #        self.context['request'].method in ['POST', 'PUT', 'PATCH']:
    #         self.fields['from_business_details'].read_only = True
    #         # Ensure it's not expected on write
    #         self.fields['from_business'].write_only = True
    #         # Ensure it's for write
    #     else: # GET
    #         # For GET, we might want to remove the 'from_business' ID field
    #         # if 'from_business_details' is present
    #         # This logic can get complex; simpler to have distinct
    #         # write_only field if strict separation is needed.
    #         # The current setup with 'from_business' (PK) and
    #         # 'from_business_details' (Nested) is common.
    #         pass


# Example of a "Light" serializer if needed for
# PurchaseItemDetailSerializer's purchase_bill field:
# class PurchaseBillLightSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PurchaseBill
#         fields = ('id', 'purchase_bill_number', 'purchase_date', 'status')
