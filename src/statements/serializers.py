from rest_framework import serializers
from .models.purchase_invoice import PurchaseBill, PurchaseItem
from .models.business import Business
from .models.logistics import Vehicle, GatePass, GatePassMovement, TripLog
from .models.support import Staff
from .models.invoice.invoice import Invoice, InvoiceStatus
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
        fields = '__all__'
        read_only_fields = ('updated_at', )


class VehicleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vehicle
        fields = '__all__'


class GatePassMovementSerializer(serializers.ModelSerializer):

    class Meta:
        model = GatePassMovement
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class GatePassSerializer(serializers.ModelSerializer):
    vehicle_details = VehicleSerializer(source='vehicle',
                                        read_only=True,
                                        allow_null=True)
    movements = GatePassMovementSerializer(many=True, read_only=True)

    class Meta:
        model = GatePass
        fields = '__all__'
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
        fields = '__all__'
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
        fields = '__all__'


class PurchaseItemDetailSerializer(PurchaseItemBaseSerializer):
    pass


class InvoiceItemSerializer(serializers.ModelSerializer):
    discount_amount = serializers.ReadOnlyField()

    class Meta:
        model = InvoiceItem
        fields = '__all__'
        read_only_fields = ['sub_total_amount', 'bill_amount', 'discount_amount']


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
        fields = '__all__'
        read_only_fields = ['total_price']


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
        fields = '__all__'
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
        fields = '__all__'
        extra_kwargs = {
            'assigned_vehicles': {
                'required': False,
                'allow_null': True
            },
            'assigned_staffs': {
                'required': False,
                'allow_null': True
            },
        }


class InvoiceSerializer(serializers.ModelSerializer):
    invoice_items = InvoiceItemSerializer(many=True)
    customer_details = BusinessSerializer(source='customer',
                                          read_only=True,
                                          allow_null=True)
    payments = PaymentSerializer(many=True, read_only=True) # Added payments

    class Meta:
        model = Invoice
        fields = '__all__'
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
        if instance.status != InvoiceStatus.DRAFT and instance.invoice_number:
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
        fields = '__all__'
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
        fields = '__all__'

class InvoicedItemStatSerializer(serializers.Serializer):
    item_name = serializers.CharField(read_only=True)
    average_price = serializers.DecimalField(max_digits=60, decimal_places=2, read_only=True)
    last_sold_price = serializers.DecimalField(max_digits=60, decimal_places=2, read_only=True)
    total_item_sold = serializers.IntegerField(read_only=True)

    class Meta:
        fields = '__all__'

class ExpensedItemStatSerializer(serializers.Serializer):
    item_name = serializers.CharField(read_only=True)
    average_price = serializers.DecimalField(max_digits=60, decimal_places=2, read_only=True)
    last_expensed_price = serializers.DecimalField(max_digits=60, decimal_places=2, read_only=True)
    total_item_expensed_quantity = serializers.DecimalField(max_digits=60, decimal_places=2, read_only=True) # quantity is DecimalField in model

    class Meta:
        fields = '__all__'

class ItemNameSerializer(serializers.Serializer):
    item_name = serializers.CharField(read_only=True)

    class Meta:
        fields = '__all__'
