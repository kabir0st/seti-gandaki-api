from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models.business import Business
from .models.logistics import GatePass, GatePassMovement, TripLog, Vehicle
from .models.purchase_invoice import PurchaseBill, PurchaseItem
from .models.invoice.invoice import Invoice
from .models.invoice.invoice_item import InvoiceItem
from .models.payments import Payment, Account
from .models.expense import ExpenseCategory, Expense, ExpenseItem
from .models.settings import StatementSettings
from .models.support import Staff
from .models.cashcounter import CashCounter
from .models.cashcounter_log import CashCounterLog

@admin.register(Business)
class BusinessAdmin(ModelAdmin):
    list_display = (
        'name',
        'registration_number',
        'current_amount',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'name',
        'registration_number',
        'contact_person',
        'contact_email',
        'phone_number',
    )
    list_filter = ('is_active', 'created_at')
    ordering = ('name', )


class PurchaseItemInline(TabularInline):
    model = PurchaseItem
    extra = 1  # Number of empty forms to display
    autocomplete_fields = [
    ]  # 'item_object' was not a ForeignKey. 'item' is a CharField.
    # Add other fields from PurchaseItem you want to be editable in-line


@admin.register(PurchaseBill)
class PurchaseBillAdmin(ModelAdmin):
    list_display = ('purchase_bill_number', 'from_business', 'purchase_date',
                    'bill_amount', 'paid_amount', 'status', 'created_at')
    list_filter = ('status', 'purchase_date', 'from_business')
    search_fields = ('purchase_bill_number', 'from_business__name', 'notes')
    autocomplete_fields = ['from_business']
    inlines = [PurchaseItemInline]
    date_hierarchy = 'purchase_date'
    ordering = ('-purchase_date', )


class InvoiceItemInline(TabularInline):
    model = InvoiceItem
    extra = 1
    autocomplete_fields = []


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = (
        'invoice_number',
        'customer_name',
        'invoiced_on',
        'bill_amount',
        'paid_amount',
        'status',
        'is_taxable',
        'created_at',
    )
    search_fields = (
        'invoice_number',
        'customer_name',
        'customer_phone_number',
        'customer_pan',
    )
    list_filter = ('status', 'is_taxable', 'invoiced_on')
    autocomplete_fields = ['customer', 'created_by', 'last_updated_by', 'cancelled_by']
    inlines = [InvoiceItemInline]
    date_hierarchy = 'invoiced_on'
    ordering = ('-invoiced_on',)


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)


class ExpenseItemInline(TabularInline):
    model = ExpenseItem
    extra = 1
    autocomplete_fields = ['attached_fuel_tickets']

@admin.register(ExpenseItem)
class ExpenseItemAdmin(ModelAdmin):
    model = ExpenseItem
    autocomplete_fields = ['attached_fuel_tickets','expense']


@admin.register(Expense)
class ExpenseAdmin(ModelAdmin):
    list_display = (
        'id',
        'category',
        'paid_to',
        'bill_number',
        'payment_date',
        'total_amount',
        'status',
        'created_by',
        'created_at',
    )
    list_filter = ('status', 'category', 'payment_date')
    search_fields = ('paid_to', 'bill_number', 'remarks')
    autocomplete_fields = ['category', 'created_by', 'last_updated_by', 'cancelled_by']
    inlines = [ExpenseItemInline]
    date_hierarchy = 'payment_date'
    ordering = ('-payment_date',)

@admin.register(PurchaseItem)
class PurchaseItemAdmin(ModelAdmin):
    list_display = ('purchase_bill', 'item_name_display', 'quantity',
                    'unit_price', 'bill_amount', 'created_at')
    list_filter = ('purchase_bill__purchase_date', 'item_description', 'item')
    search_fields = ('item_description', 'item',
                     'purchase_bill__purchase_bill_number')
    autocomplete_fields = ['purchase_bill'
                           ]  # 'item_object' removed as it's not a ForeignKey
    ordering = ('-purchase_bill__purchase_date', 'id')

    def item_name_display(self, obj):
        # 'item_object' does not exist on the model.
        # Display 'item_description' or 'item'.
        return obj.item_description or obj.item

    item_name_display.short_description = 'Item Name'

    # 'item' is a CharField. If a related 'Item' model and ForeignKey
    # were intended for 'item_object', the model structure would need changes.


@admin.register(Vehicle)
class VehicleAdmin(ModelAdmin):
    list_display = ('license_plate', 'is_active', 'created_at')
    search_fields = ('license_plate', )
    list_filter = ('is_active', )
    # autocomplete_fields = ['business'] # Business FK removed
    ordering = ('license_plate', )


class GatePassMovementInline(TabularInline):
    model = GatePassMovement
    extra = 0  # Show existing movements, don't add new ones by default here
    readonly_fields = ('created_at', 'updated_at', 'exit_time', 'entry_time')

    # Can't directly edit exit/entry time here as they are set by API actions.
    # To allow manual override, remove from readonly_fields and ensure
    # proper handling.

    def has_add_permission(self, request, obj=None):
        return False  # Movements are created via API actions

    def has_change_permission(self, request, obj=None):
        return False  # Movements are primarily managed via API

    def has_delete_permission(self, request, obj=None):
        # Allow deletion if necessary, but consider implications
        return True  # Or False, depending on policy


@admin.register(GatePass)
class GatePassAdmin(ModelAdmin):
    list_display = ('vehicle', 'license_plate', 'driver_name', 'issued_by',
                    'purpose', 'created_at', 'get_last_movement_time',
                    'get_last_movement_type')
    search_fields = ('vehicle__license_plate', 'license_plate', 'driver_name',
                     'purpose', 'remarks')
    list_filter = ('created_at', 'vehicle', 'issued_by')
    autocomplete_fields = ['vehicle', 'issued_by']
    date_hierarchy = 'created_at'  # Was 'entry_time'
    ordering = ('-created_at', )  # Was '-entry_time'
    inlines = [GatePassMovementInline]
    readonly_fields = ('created_at', 'updated_at')

    def get_last_movement_time(self, obj):
        last_movement = obj.movements.order_by('-created_at').first()
        if last_movement:
            return last_movement.exit_time or last_movement.entry_time
        return None

    get_last_movement_time.short_description = 'Last Movement Time'

    def get_last_movement_type(self, obj):
        last_movement = obj.movements.order_by('-created_at').first()
        if last_movement:
            return "Exit" if last_movement.exit_time else "Entry"
        return "N/A"

    get_last_movement_type.short_description = 'Last Movement Type'


@admin.register(TripLog)
class TripLogAdmin(ModelAdmin):
    list_display = ('gate_pass__vehicle__license_plate', 'for_purchase_bill',
                    'purpose', 'created_at')
    # Removed fields: start_time, end_time, start_location, end_location,
    # driver_display, gate_pass, distance_km, duration_hours
    search_fields = ('gate_pass__vehicle__license_plate',
                     'for_purchase_bill__purchase_bill_number', 'purpose',
                     'notes')
    # Removed start_location, end_location, driver__username, driver_name_text
    list_filter = ('created_at', 'for_purchase_bill')
    # Removed start_time, driver, gate_pass
    autocomplete_fields = ['gate_pass', 'for_purchase_bill']
    # Removed gate_pass, driver
    date_hierarchy = 'created_at'  # Was 'start_time'
    ordering = ('-created_at', )  # Was '-start_time'


@admin.register(StatementSettings)
class StatementSettingsAdmin(ModelAdmin):
    list_display = ('fiscal_year_change_month_in_bs',
                    'fiscal_year_change_day_in_bs',
                    'default_quick_invoice_business', 'sales_note')
    autocomplete_fields = ['default_quick_invoice_business']


@admin.register(Staff)
class StaffAdmin(ModelAdmin):
    list_display = ('name', 'phone_number', 'pan', 'enrollment_date', 'assigned_salary',
                    'updated_at')
    search_fields = ('name', 'phone_number', 'pan')
    list_filter = ('updated_at', )
    ordering = ('name', )

    # driver_display method removed as driver fields are no longer on TripLog

@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = (
        'id',
        'action',
        'amount',
        'header',
        'related_business__name',
        'related_account__name',
        'created_at',
    )
    list_filter = ( 'is_refunded', 'created_at', 'invoice', 'purchase_bill', 'expense')
    search_fields = (
        'id',
        'created_by__username', # Assuming UserBase has a username field
        'invoice__invoice_number',
        'purchase_bill__purchase_bill_number',
        'expense__bill_number', # Assuming Expense has a bill_number
        'remarks',
    )
    autocomplete_fields = ['created_by', 'invoice', 'purchase_bill', 'expense']


@admin.register(Account)
class AccountAdmin(ModelAdmin):
    list_display = (
        'name',
        'account_number',
        'bank_name',
        'current_amount',
        'created_at',
        'updated_at',
    )
    search_fields = ('name', 'account_number', 'bank_name', 'branch_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('name',)


class CashCounterLogInline(TabularInline):
    model = CashCounterLog
    extra = 0
    readonly_fields = ('created_at', 'pre_amount', 'final_amount', 'is_applied')
    fields = (
        'denomination_1000', 'denomination_500', 'denomination_100',
        'denomination_50', 'denomination_20', 'denomination_10',
        'denomination_5', 'denomination_2', 'denomination_1',
        'remarks', 'pre_amount', 'final_amount', 'is_applied', 'created_at'
    )

    def has_change_permission(self, request, obj=None):
        return False  # Logs should not be modified after creation


@admin.register(CashCounter)
class CashCounterAdmin(ModelAdmin):
    list_display = (
        'counter_name',
        'get_total_amount',
        'denomination_1000',
        'denomination_500',
        'denomination_100',
    )
    search_fields = ('counter_name',)
    ordering = ('counter_name',)
    inlines = [CashCounterLogInline]

    fieldsets = (
        (None, {
            'fields': ('counter_name',)
        }),
        ('High Denominations', {
            'fields': ('denomination_1000', 'denomination_500', 'denomination_100')
        }),
        ('Medium Denominations', {
            'fields': ('denomination_50', 'denomination_20', 'denomination_10')
        }),
        ('Low Denominations', {
            'fields': ('denomination_5', 'denomination_2', 'denomination_1')
        }),
    )

    def get_total_amount(self, obj):
        return f"Rs. {obj.total_amount():,.2f}"
    get_total_amount.short_description = 'Total Amount'


@admin.register(CashCounterLog)
class CashCounterLogAdmin(ModelAdmin):
    list_display = (
        'cash_counter',
        'get_total_change',
        'pre_amount',
        'final_amount',
        'is_applied',
        'created_at',
    )
    list_filter = ('is_applied', 'created_at', 'cash_counter')
    search_fields = ('cash_counter__counter_name', 'remarks')
    readonly_fields = ('created_at', 'pre_amount', 'final_amount', 'is_applied')
    autocomplete_fields = ['cash_counter']
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': ('cash_counter', 'remarks')
        }),
        ('High Denominations Changes', {
            'fields': ('denomination_1000', 'denomination_500', 'denomination_100')
        }),
        ('Medium Denominations Changes', {
            'fields': ('denomination_50', 'denomination_20', 'denomination_10')
        }),
        ('Low Denominations Changes', {
            'fields': ('denomination_5', 'denomination_2', 'denomination_1')
        }),
        ('Summary', {
            'fields': ('pre_amount', 'final_amount', 'is_applied'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_total_change(self, obj):
        change = obj.calculate_total_change()
        return f"Rs. {change:+,.2f}"
    get_total_change.short_description = 'Total Change'

    def has_change_permission(self, request, obj=None):
        # Prevent modification of existing logs
        if obj and obj.pk:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of applied logs
        if obj and obj.is_applied:
            return False
        return super().has_delete_permission(request, obj)
