from django.contrib import admin
from .models.purchase_invoice import PurchaseBill, PurchaseItem
from .models.business import Business
from .models.logistics import Vehicle, GatePass, TripLog
from unfold.admin import ModelAdmin, TabularInline


@admin.register(Business)
class BusinessAdmin(ModelAdmin):
    list_display = (
        'name',
        'registration_number',
        'contact_person',
        'contact_email',
        'phone_number',
        'is_active',
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
    autocomplete_fields = ['from_business'
                           ]  # Assuming 'from_business' is a ForeignKey
    inlines = [PurchaseItemInline]
    date_hierarchy = 'purchase_date'
    ordering = ('-purchase_date', )


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


@admin.register(GatePass)
class GatePassAdmin(ModelAdmin):
    list_display = ('vehicle', 'license_plate', 'entry_time', 'exit_time',
                    'driver_name', 'issued_by', 'purpose'
                    )  # Removed business, destination
    search_fields = ('vehicle__license_plate', 'license_plate', 'driver_name',
                     'purpose', 'remarks'
                     )  # Removed business__name, destination
    list_filter = ('entry_time', 'exit_time', 'vehicle')  # Removed business
    autocomplete_fields = ['vehicle', 'issued_by']  # Removed business
    date_hierarchy = 'entry_time'
    ordering = ('-entry_time', )


@admin.register(TripLog)
class TripLogAdmin(ModelAdmin):
    list_display = ('vehicle', 'for_purchase_bill', 'purpose', 'created_at')
    # Removed fields: start_time, end_time, start_location, end_location,
    # driver_display, gate_pass, distance_km, duration_hours
    search_fields = ('vehicle__license_plate',
                     'for_purchase_bill__purchase_bill_number', 'purpose',
                     'notes')
    # Removed start_location, end_location, driver__username, driver_name_text
    list_filter = ('created_at', 'vehicle', 'for_purchase_bill')
    # Removed start_time, driver, gate_pass
    autocomplete_fields = ['vehicle', 'for_purchase_bill']
    # Removed gate_pass, driver
    date_hierarchy = 'created_at'  # Was 'start_time'
    ordering = ('-created_at', )  # Was '-start_time'

    # driver_display method removed as driver fields are no longer on TripLog
