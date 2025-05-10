from django.contrib import admin
from .models.purchase_invoice import PurchaseBill, PurchaseItem
from .models.business import Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
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


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1  # Number of empty forms to display
    autocomplete_fields = [
    ]  # 'item_object' was not a ForeignKey. 'item' is a CharField.
    # Add other fields from PurchaseItem you want to be editable in-line


@admin.register(PurchaseBill)
class PurchaseBillAdmin(admin.ModelAdmin):
    list_display = ('purchase_bill_number', 'from_business', 'purchase_date',
                    'bill_amount', 'paid_amount', 'status', 'created_at')
    list_filter = ('status', 'purchase_date', 'from_business')
    search_fields = ('purchase_bill_number', 'from_business__name', 'notes')
    autocomplete_fields = ['from_business'
                           ]  # Assuming 'from_business' is a ForeignKey
    inlines = [PurchaseItemInline]
    date_hierarchy = 'purchase_date'
    ordering = ('-purchase_date', )

    fieldsets = (
        (None, {
            'fields': ('purchase_bill_number', 'from_business',
                       'purchase_date', 'due_date')
        }),
        ('Amount Details', {
            'fields':
            ('bill_amount', 'paid_amount', 'discount_amount', 'tax_amount')
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes')
        }),
    )
    # Add readonly_fields if necessary, e.g., for calculated fields
    # readonly_fields = ('',)


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
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
