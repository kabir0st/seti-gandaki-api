import django_filters
from django_filters import rest_framework as filters

from statements.models.invoice import Invoice, InvoiceItem, InvoiceStatus
from statements.models.business import Business
from system.models import UserBase


class InvoiceFilterSet(filters.FilterSet):
    # User filters
    created_by = filters.ModelChoiceFilter(queryset=UserBase.objects.all())
    last_updated_by = filters.ModelChoiceFilter(queryset=UserBase.objects.all())
    cancelled_by = filters.ModelChoiceFilter(queryset=UserBase.objects.all())
    
    # Customer filters
    customer = filters.ModelChoiceFilter(queryset=Business.objects.all())
    customer_name = filters.CharFilter(lookup_expr='icontains')
    customer_phone_number = filters.CharFilter(lookup_expr='icontains')
    customer_pan = filters.CharFilter(lookup_expr='icontains')
    
    # Invoice details
    invoice_number = filters.CharFilter(lookup_expr='icontains')
    status = filters.ChoiceFilter(choices=InvoiceStatus.choices)
    
    # Date filters - From date to Date filter as requested
    invoiced_on_after = filters.DateFilter(field_name='invoiced_on', lookup_expr='date__gte')
    invoiced_on_before = filters.DateFilter(field_name='invoiced_on', lookup_expr='date__lte')
    
    due_on_after = filters.DateFilter(field_name='due_on', lookup_expr='date__gte')
    due_on_before = filters.DateFilter(field_name='due_on', lookup_expr='date__lte')
    
    created_at_after = filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_at_before = filters.DateFilter(field_name='created_at', lookup_expr='date__lte')
    
    # Amount filters
    bill_amount_min = filters.NumberFilter(field_name='bill_amount', lookup_expr='gte')
    bill_amount_max = filters.NumberFilter(field_name='bill_amount', lookup_expr='lte')
    
    paid_amount_min = filters.NumberFilter(field_name='paid_amount', lookup_expr='gte')
    paid_amount_max = filters.NumberFilter(field_name='paid_amount', lookup_expr='lte')
    
    sub_total_amount_min = filters.NumberFilter(field_name='sub_total_amount', lookup_expr='gte')
    sub_total_amount_max = filters.NumberFilter(field_name='sub_total_amount', lookup_expr='lte')
    
    # Boolean filters
    is_paid = filters.BooleanFilter()
    is_taxable = filters.BooleanFilter()
    
    # Delivery filters
    delivery_location = filters.CharFilter(lookup_expr='icontains')
    tracking_code = filters.CharFilter(lookup_expr='icontains')
    
    # Fiscal year filters
    fiscal_year_ad = filters.CharFilter(lookup_expr='exact')
    fiscal_year_bs = filters.CharFilter(lookup_expr='exact')

    class Meta:
        model = Invoice
        fields = [
            'created_by',
            'last_updated_by',
            'cancelled_by',
            'customer',
            'customer_name',
            'customer_phone_number',
            'customer_pan',
            'invoice_number',
            'status',
            'invoiced_on_after',
            'invoiced_on_before',
            'due_on_after',
            'due_on_before',
            'created_at_after',
            'created_at_before',
            'bill_amount_min',
            'bill_amount_max',
            'paid_amount_min',
            'paid_amount_max',
            'sub_total_amount_min',
            'sub_total_amount_max',
            'is_paid',
            'is_taxable',
            'delivery_location',
            'tracking_code',
            'fiscal_year_ad',
            'fiscal_year_bs',
        ]


class InvoiceItemFilterSet(filters.FilterSet):
    # Invoice filter
    invoice = filters.ModelChoiceFilter(queryset=Invoice.objects.all())
    
    # Item details
    item_name = filters.CharFilter(lookup_expr='icontains')
    unit = filters.CharFilter(lookup_expr='icontains')
    
    # Quantity filters
    quantity_min = filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    quantity_max = filters.NumberFilter(field_name='quantity', lookup_expr='lte')
    
    # Price filters
    price_per_item_min = filters.NumberFilter(field_name='price_per_item', lookup_expr='gte')
    price_per_item_max = filters.NumberFilter(field_name='price_per_item', lookup_expr='lte')
    
    # Amount filters
    sub_total_amount_min = filters.NumberFilter(field_name='sub_total_amount', lookup_expr='gte')
    sub_total_amount_max = filters.NumberFilter(field_name='sub_total_amount', lookup_expr='lte')
    
    bill_amount_min = filters.NumberFilter(field_name='bill_amount', lookup_expr='gte')
    bill_amount_max = filters.NumberFilter(field_name='bill_amount', lookup_expr='lte')
    
    # Discount filters
    discount_percent_min = filters.NumberFilter(field_name='discount_percent', lookup_expr='gte')
    discount_percent_max = filters.NumberFilter(field_name='discount_percent', lookup_expr='lte')
    
    discount_remarks = filters.CharFilter(lookup_expr='icontains')
    
    # Boolean filters
    is_marked_as_complete = filters.BooleanFilter()
    
    # Date filters
    created_at_after = filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_at_before = filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = InvoiceItem
        fields = [
            'invoice',
            'item_name',
            'unit',
            'quantity_min',
            'quantity_max',
            'price_per_item_min',
            'price_per_item_max',
            'sub_total_amount_min',
            'sub_total_amount_max',
            'bill_amount_min',
            'bill_amount_max',
            'discount_percent_min',
            'discount_percent_max',
            'discount_remarks',
            'is_marked_as_complete',
            'created_at_after',
            'created_at_before',
        ]