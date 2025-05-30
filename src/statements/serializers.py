from rest_framework import serializers
from .models.purchase_invoice import PurchaseBill, PurchaseItem
from .models.business import Business
from .models.logistics import Vehicle, GatePass, GatePassMovement, TripLog
from .models.support import Staff
from .models.invoice.invoice import Invoice
from .models.invoice.invoice_item import InvoiceItem
from .models.settings import StatementSettings
from .models.expense import ExpenseCategory, Expense, ExpenseItem
from .models.payments import Payment


# Serializer for Business model
class BusinessSerializer(serializers.ModelSerializer):

    class Meta:
        model = Business
        fields = '__all__'


class StaffSerializer(serializers.ModelSerializer):

    class Meta:
        model = Staff
        fields = [
            'id', 'name', 'phone_number', 'verification_document', 'pan',
            'assigned_salary', 'address', 'enrollment_date', 'updated_at'
        ]
        read_only_fields = ('updated_at', )


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
    gate_pass_details = GatePassSerializer(source='gate_pass', read_only=True)

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


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = [
            'id',
            'item_name',
            'quantity',
            'unit',
            'price_per_item',
            'discount_percent',
            'discount_remarks',
            'sub_total_amount',
            'bill_amount',
        ]
        read_only_fields = ['sub_total_amount', 'bill_amount']


class InvoiceSerializer(serializers.ModelSerializer):
    invoice_items = InvoiceItemSerializer(many=True)
    customer_details = BusinessSerializer(source='customer',
                                          read_only=True,
                                          allow_null=True)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'created_by',
            'last_updated_by',
            'cancelled_by',
            'customer',
            'customer_details',
            'customer_name',
            'customer_phone_number',
            'customer_pan',
            'invoiced_on',
            'due_on',
            'invoice_number',
            'status',
            'delivery_charge',
            'delivery_location',
            'delivery_note',
            'tracking_code',
            'weight_unit',
            'total_weight',
            'additional_charge_amount',
            'additional_charge_note',
            'additional_discount_amount',
            'additional_discount_note',
            'sub_total_amount',
            'total_discount_amount',
            'total_taxable_amount',
            'total_tax_amount',
            'bill_amount',
            'paid_amount',
            'serial',
            'fiscal_year_ad',
            'fiscal_year_bs',
            'is_paid',
            'remarks',
            'is_taxable',
            'invoice_items',
        ]
        read_only_fields = [
            'invoice_number',
            'sub_total_amount',
            'total_discount_amount',
            'total_taxable_amount',
            'total_tax_amount',
            'bill_amount',
            'paid_amount',
            'serial',
            'fiscal_year_ad',
            'fiscal_year_bs',
            'is_paid',
        ]

    def create(self, validated_data):
        invoice_items_data = validated_data.pop('invoice_items')
        invoice = Invoice.objects.create(**validated_data)
        for item_data in invoice_items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        return invoice

    def update(self, instance, validated_data):
        # Prevent changing is_taxable if invoice is not in draft and has an invoice number
        if instance.status != Invoice.InvoiceStatus.DRAFT and instance.invoice_number:
            if 'is_taxable' in validated_data and validated_data['is_taxable'] != instance.is_taxable:
                raise serializers.ValidationError("Cannot change 'is_taxable' once invoice is approved and has an invoice number.")

        invoice_items_data = validated_data.pop('invoice_items', [])

        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update or create invoice items
        # This is a simplified approach. For more robust handling (e.g., deleting removed items),
        # you'd need more complex logic.
        for item_data in invoice_items_data:
            item_id = item_data.get('id')
            if item_id:
                try:
                    invoice_item = InvoiceItem.objects.get(id=item_id, invoice=instance)
                    for attr, value in item_data.items():
                        setattr(invoice_item, attr, value)
                    invoice_item.save()
                except InvoiceItem.DoesNotExist:
                    # Handle case where item_id is provided but doesn't exist for this invoice
                    pass
            else:
                InvoiceItem.objects.create(invoice=instance, **item_data)

        return instance


class StatementSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatementSettings
        fields = '__all__'


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'


class ExpenseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseItem
        fields = [
            'id',
            'item_name',
            'quantity',
            'price_per_item',
            'total_price',
        ]
        read_only_fields = ['total_amount']


class PaymentSerializer(serializers.ModelSerializer):
    created_by_details = serializers.StringRelatedField(source='created_by', read_only=True, allow_null=True)
    # To avoid circular dependency, we will use StringRelatedField or PrimaryKeyRelatedField for related models
    # or define them as forward references if DRF version supports it well.
    # For now, let's defer full nested serializers for invoice/purchase_bill/expense details within payment
    # to avoid complexity or ensure they are defined before PaymentSerializer.
    # We can add simple string representations or IDs.
    # invoice_details = InvoiceSerializer(source='invoice', read_only=True, allow_null=True) # Potential circular import
    # purchase_bill_details = PurchaseBillSerializer(source='purchase_bill', read_only=True, allow_null=True) # Potential circular import
    # expense_details = ExpenseSerializer(source='expense', read_only=True, allow_null=True) # Potential circular import
    payment_for = serializers.ReadOnlyField()

    class Meta:
        model = Payment
        fields = [
            'id',
            'created_by',
            'created_by_details',
            'header',
            'invoice', # FK ID
            'purchase_bill', # FK ID
            'expense', # FK ID
            'amount',
            'remarks',
            'receipt',
            'is_refunded',
            'payment_for', # Property method
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('created_at', 'updated_at', 'payment_for')
        extra_kwargs = {
            'invoice': {'allow_null': True, 'required': False},
            'purchase_bill': {'allow_null': True, 'required': False},
            'expense': {'allow_null': True, 'required': False},
            'created_by': {'allow_null': True, 'required': False},
        }

    def validate(self, data):
        related_objects = ['invoice', 'purchase_bill', 'expense']
        provided_relations = [obj for obj in related_objects if data.get(obj)]

        if len(provided_relations) == 0:
            pass # Allowing manual payments

        if len(provided_relations) > 1:
            raise serializers.ValidationError(
                "A payment can only be associated with one of: Invoice, Purchase Bill, or Expense."
            )
        return data


# Serializer for PurchaseBill
class PurchaseBillSerializer(serializers.ModelSerializer):
    purchase_items = PurchaseItemBaseSerializer(many=True, read_only=True)
    from_business_details = BusinessSerializer(source='from_business',
                                               read_only=True,
                                               allow_null=True)
    from_business = serializers.PrimaryKeyRelatedField(
        queryset=Business.objects.all(),
        allow_null=True,
        required=False,
    )
    payments = PaymentSerializer(many=True, read_only=True) # Added payments

    class Meta:
        model = PurchaseBill
        fields = (
            'id',
            'purchase_date',
            'from_business',
            'from_business_details',
            'purchase_bill_number',
            'sub_total',
            'grace_discount',
            'shipping_and_handling_costs',
            'additional_costs',
            'additional_costs_remarks',
            'bill_amount',
            'paid_amount',
            'shipping_handling_receipt',
            'status',
            'purchase_receipt',
            'notes',
            'created_at',
            'updated_at',
            'purchase_items',
            'payments' # Added payments
        )
        read_only_fields = (
            'sub_total',
            'bill_amount',
        )


class InvoiceSerializer(serializers.ModelSerializer):
    invoice_items = InvoiceItemSerializer(many=True)
    customer_details = BusinessSerializer(source='customer',
                                          read_only=True,
                                          allow_null=True)
    payments = PaymentSerializer(many=True, read_only=True) # Added payments

    class Meta:
        model = Invoice
        fields = [
            'id',
            'created_by',
            'last_updated_by',
            'cancelled_by',
            'customer',
            'customer_details',
            'customer_name',
            'customer_phone_number',
            'customer_pan',
            'invoiced_on',
            'due_on',
            'invoice_number',
            'status',
            'delivery_charge',
            'delivery_location',
            'delivery_note',
            'tracking_code',
            'weight_unit',
            'total_weight',
            'additional_charge_amount',
            'additional_charge_note',
            'additional_discount_amount',
            'additional_discount_note',
            'sub_total_amount',
            'total_discount_amount',
            'total_taxable_amount',
            'total_tax_amount',
            'bill_amount',
            'paid_amount',
            'serial',
            'fiscal_year_ad',
            'fiscal_year_bs',
            'is_paid',
            'remarks',
            'is_taxable',
            'invoice_items',
            'payments', # Added payments
        ]
        read_only_fields = [
            'invoice_number',
            'sub_total_amount',
            'total_discount_amount',
            'total_taxable_amount',
            'total_tax_amount',
            'bill_amount',
            'paid_amount',
            'serial',
            'fiscal_year_ad',
            'fiscal_year_bs',
            'is_paid',
        ]

    def create(self, validated_data):
        invoice_items_data = validated_data.pop('invoice_items')
        invoice = Invoice.objects.create(**validated_data)
        for item_data in invoice_items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        return invoice

    def update(self, instance, validated_data):
        if instance.status != Invoice.InvoiceStatus.DRAFT and instance.invoice_number:
            if 'is_taxable' in validated_data and validated_data['is_taxable'] != instance.is_taxable:
                raise serializers.ValidationError("Cannot change 'is_taxable' once invoice is approved and has an invoice number.")

        invoice_items_data = validated_data.pop('invoice_items', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for item_data in invoice_items_data:
            item_id = item_data.get('id')
            if item_id:
                try:
                    invoice_item = InvoiceItem.objects.get(id=item_id, invoice=instance)
                    for attr, value in item_data.items():
                        setattr(invoice_item, attr, value)
                    invoice_item.save()
                except InvoiceItem.DoesNotExist:
                    pass
            else:
                InvoiceItem.objects.create(invoice=instance, **item_data)

        return instance


class StatementSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatementSettings
        fields = '__all__'


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'


# Note: PaymentSerializer was moved up


class ExpenseSerializer(serializers.ModelSerializer):
    expense_items = ExpenseItemSerializer(many=True)
    payments = PaymentSerializer(many=True, read_only=True) # Added payments

    class Meta:
        model = Expense
        fields = [
            'id',
            'category',
            'paid_to',
            'bill_number',
            'payment_date',
            'total_amount',
            'status',
            'remarks',
            'created_by',
            'last_updated_by',
            'cancelled_by',
            'created_at',
            'updated_at',
            'expense_items',
            'payments', # Added payments
        ]
        read_only_fields = ['total_amount']

    def create(self, validated_data):
        expense_items_data = validated_data.pop('expense_items')
        expense = Expense.objects.create(**validated_data)
        for item_data in expense_items_data:
            ExpenseItem.objects.create(expense=expense, **item_data)
        return expense

    def update(self, instance, validated_data):
        expense_items_data = validated_data.pop('expense_items', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for item_data in expense_items_data:
            item_id = item_data.get('id')
            if item_id:
                try:
                    expense_item = ExpenseItem.objects.get(id=item_id, expense=instance)
                    for attr, value in item_data.items():
                        setattr(expense_item, attr, value)
                    expense_item.save()
                except ExpenseItem.DoesNotExist:
                    pass
            else:
                ExpenseItem.objects.create(expense=instance, **item_data)

        return instance
class PurchasedItemStatSerializer(serializers.Serializer):
    item_name = serializers.CharField(read_only=True)
    average_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    last_bought_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_item_bought = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        fields = [
            'item_name',
            'average_price',
            'last_bought_price',
            'total_item_bought',
        ]

class InvoicedItemStatSerializer(serializers.Serializer):
    item_name = serializers.CharField(read_only=True)
    average_price = serializers.DecimalField(max_digits=60, decimal_places=2, read_only=True)
    last_sold_price = serializers.DecimalField(max_digits=60, decimal_places=2, read_only=True)
    total_item_sold = serializers.IntegerField(read_only=True)

    class Meta:
        fields = [
            'item_name',
            'average_price',
            'last_sold_price',
            'total_item_sold',
        ]

class ExpensedItemStatSerializer(serializers.Serializer):
    item_name = serializers.CharField(read_only=True)
    average_price = serializers.DecimalField(max_digits=60, decimal_places=2, read_only=True)
    last_expensed_price = serializers.DecimalField(max_digits=60, decimal_places=2, read_only=True)
    total_item_expensed_quantity = serializers.DecimalField(max_digits=60, decimal_places=2, read_only=True) # quantity is DecimalField in model

    class Meta:
        fields = [
            'item_name',
            'average_price',
            'last_expensed_price',
            'total_item_expensed_quantity',
        ]

class ItemNameSerializer(serializers.Serializer):
    item_name = serializers.CharField(read_only=True)

    class Meta:
        fields = ['item_name']
