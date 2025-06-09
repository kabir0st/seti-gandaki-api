import datetime
from django.utils import timezone
from rest_framework import serializers
from decimal import Decimal
from django.db.models import Q # Q can be useful for complex queries
from hrm.models.fuel import FuelTicket
from statements.models.cashcounter import CashCounter
from statements.models.cashcounter_log import CashCounterLog
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
        extra_kwargs = {
            'invoice': {'required': False, 'allow_null': True}  # For nested creation, parent provides. For direct, client must.
        }


class StatementSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatementSettings
        fields = '__all__'


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'


class ExpenseItemSerializer(serializers.ModelSerializer):
    assigned_fuel_ticket_filters = serializers.JSONField(
        write_only=True, required=False, allow_null=True
    )
    # attached_fuel_tickets will be handled by PrimaryKeyRelatedField by default
    # It expects a list of PKs and resolves to instances in validated_data

    class Meta:
        model = ExpenseItem
        fields = '__all__'
        read_only_fields = ['total_price', 'expense'] # total_price is calculated by model's save

    def _process_fuel_tickets(self, filters_data):
        if not filters_data or not isinstance(filters_data, dict):
            return [], Decimal('0.00')

        has_valid_filters = False
        fuel_ticket_qs = FuelTicket.objects.filter(is_consumed=True)
        
        if 'ids' in filters_data:
            has_valid_filters = True
            ids = filters_data['ids']
            if not isinstance(ids, list):
                raise serializers.ValidationError({"assigned_fuel_ticket_filters": "ids must be a list."})
            fuel_ticket_qs = fuel_ticket_qs.filter(id__in=ids)
        else:
            station_id = filters_data.get('consumed_by_station')
            if station_id is not None:
                has_valid_filters = True
                fuel_ticket_qs = fuel_ticket_qs.filter(consumed_by_station_id=station_id)
            
            date_range_str = filters_data.get('consumed_at__range')
            if date_range_str:
                has_valid_filters = True
                if not (isinstance(date_range_str, list) and len(date_range_str) == 2):
                    raise serializers.ValidationError({"assigned_fuel_ticket_filters": "consumed_at__range must be a list of two date/datetime strings."})
                fuel_ticket_qs = fuel_ticket_qs.filter(consumed_at__range=date_range_str)
            
            # Add other potential filters here and set has_valid_filters = True

        if not has_valid_filters:
            return [], Decimal('0.00')

        selected_tickets = list(fuel_ticket_qs)
        # Ensure all selected tickets are indeed consumed (double check)
        for ticket in selected_tickets:
            if not ticket.is_consumed:
                 # This case should ideally not be hit if the initial filter `is_consumed=True` is effective
                raise serializers.ValidationError(
                    f"Fuel ticket {ticket.ticket_id} was selected but is not marked as consumed. Please check data integrity or filter logic."
                )
        total_bill = sum(ticket.bill_amount for ticket in selected_tickets) if selected_tickets else Decimal('0.00')
        
        return selected_tickets, total_bill

    def create(self, validated_data):
        assigned_filters = validated_data.pop('assigned_fuel_ticket_filters', None)
        # validated_data['attached_fuel_tickets'] will contain FuelTicket instances if provided
        manually_attached_ticket_instances = validated_data.pop('attached_fuel_tickets', None)

        final_tickets_to_attach_instances = []
        
        if assigned_filters:
            selected_tickets, total_bill = self._process_fuel_tickets(assigned_filters)
            validated_data['item_name'] = validated_data.get('item_name', "Fuel Expense (from filters)")
            validated_data['quantity'] = Decimal('1.00')
            validated_data['price_per_item'] = total_bill
            final_tickets_to_attach_instances = selected_tickets
        elif manually_attached_ticket_instances is not None:
            valid_manual_tickets = []
            for ticket_instance in manually_attached_ticket_instances:
                if not ticket_instance.is_consumed:
                    raise serializers.ValidationError(
                        f"Manually attached fuel ticket {ticket_instance.ticket_id} is not consumed."
                    )
                valid_manual_tickets.append(ticket_instance)
            
            final_tickets_to_attach_instances = valid_manual_tickets
            
            if 'price_per_item' not in validated_data and 'quantity' not in validated_data:
                 total_bill_manual = sum(t.bill_amount for t in valid_manual_tickets) if valid_manual_tickets else Decimal('0.00')
                 validated_data['item_name'] = validated_data.get('item_name', "Fuel Expense (manual attach)")
                 validated_data['quantity'] = Decimal('1.00')
                 validated_data['price_per_item'] = total_bill_manual
        
        # Model's save method will calculate total_price based on quantity and price_per_item
        expense_item = super().create(validated_data)

        if final_tickets_to_attach_instances:
            expense_item.attached_fuel_tickets.set(final_tickets_to_attach_instances)
        
        return expense_item

    def update(self, instance, validated_data):
        assigned_filters = validated_data.pop('assigned_fuel_ticket_filters', None)
        manually_attached_ticket_instances = validated_data.pop('attached_fuel_tickets', None)

        final_tickets_to_attach_instances = list(instance.attached_fuel_tickets.all())
        should_update_attachments = False

        if assigned_filters:
            selected_tickets, total_bill = self._process_fuel_tickets(assigned_filters)
            # Update instance fields that will be used by model's save()
            instance.item_name = validated_data.get('item_name', instance.item_name)
            instance.quantity = Decimal('1.00')
            instance.price_per_item = total_bill
            final_tickets_to_attach_instances = selected_tickets
            should_update_attachments = True
        elif manually_attached_ticket_instances is not None:
            valid_manual_tickets = []
            for ticket_instance in manually_attached_ticket_instances:
                if not ticket_instance.is_consumed:
                    raise serializers.ValidationError(
                        f"Manually attached fuel ticket {ticket_instance.ticket_id} is not consumed."
                    )
                valid_manual_tickets.append(ticket_instance)
            
            final_tickets_to_attach_instances = valid_manual_tickets
            should_update_attachments = True
            
            if 'price_per_item' not in validated_data and 'quantity' not in validated_data:
                 total_bill_manual = sum(t.bill_amount for t in valid_manual_tickets) if valid_manual_tickets else Decimal('0.00')
                 instance.item_name = validated_data.get('item_name', instance.item_name)
                 instance.quantity = Decimal('1.00')
                 instance.price_per_item = total_bill_manual
        
        # Apply other validated data to the instance fields
        # Note: instance.quantity and instance.price_per_item might have been set above
        for key, value in validated_data.items():
            setattr(instance, key, value)
        
        # Save the instance. Model's save() will recalculate total_price.
        instance.save()

        if should_update_attachments:
            instance.attached_fuel_tickets.set(final_tickets_to_attach_instances)
        
        return instance


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
    payments = PaymentSerializer(many=True, read_only=True)
    purchase_date = serializers.DateField()
    bill_started_from = serializers.DateField(required=False, allow_null=True)
    bill_completed_on = serializers.DateField(required=False, allow_null=True)

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

class MiniExpenseSerializer(serializers.ModelSerializer):
    """
    A minimal serializer for Expense model, used in nested representations.
    """
    class Meta:
        model = Expense
        fields = ('id', 'expense_number', 'expense_date', 'total_amount', 'category')

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
class CashCounterSerializer(serializers.ModelSerializer):
    """
    Serializer for the CashCounter model.
    """
    class Meta:
        model = CashCounter
        fields = '__all__'
class CashCounterLogSerializer(serializers.ModelSerializer):
    """
    Serializer for the CashCounterLog model.
    """
    class Meta:
        model = CashCounterLog
        fields = '__all__'
        read_only_fields = ('pre_amount', 'final_amount', 'created_at', 'is_applied') # These fields are set by the model/signals
