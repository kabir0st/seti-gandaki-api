import django_filters
from django_filters import rest_framework as filters

from statements.models.expense import Expense, ExpenseItem, ExpenseCategory, ExpenseStatus
from system.models import UserBase


class ExpenseFilterSet(filters.FilterSet):
    created_by = filters.ModelChoiceFilter(queryset=UserBase.objects.all())
    category = filters.ModelChoiceFilter(queryset=ExpenseCategory.objects.all())
    paid_to = filters.CharFilter(lookup_expr='icontains')
    bill_number = filters.CharFilter(lookup_expr='icontains')
    status = filters.ChoiceFilter(choices=ExpenseStatus.choices)
    is_paid = filters.BooleanFilter()

    payment_date_after = filters.DateFilter(field_name='payment_date', lookup_expr='date__gte')
    payment_date_before = filters.DateFilter(field_name='payment_date', lookup_expr='date__lte')

    created_at_after = filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_at_before = filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    total_amount_min = filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount_max = filters.NumberFilter(field_name='total_amount', lookup_expr='lte')

    class Meta:
        model = Expense
        fields = [
            'created_by',
            'category',
            'paid_to',
            'bill_number',
            'status',
            'is_paid',
            'payment_date_after',
            'payment_date_before',
            'created_at_after',
            'created_at_before',
            'total_amount_min',
            'total_amount_max',
        ]


class ExpenseItemFilterSet(filters.FilterSet):
    expense = filters.ModelChoiceFilter(queryset=Expense.objects.all())
    item_name = filters.CharFilter(lookup_expr='icontains')

    quantity_min = filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    quantity_max = filters.NumberFilter(field_name='quantity', lookup_expr='lte')

    price_per_item_min = filters.NumberFilter(field_name='price_per_item', lookup_expr='gte')
    price_per_item_max = filters.NumberFilter(field_name='price_per_item', lookup_expr='lte')

    total_price_min = filters.NumberFilter(field_name='total_price', lookup_expr='gte')
    total_price_max = filters.NumberFilter(field_name='total_price', lookup_expr='lte')
    
    created_at_after = filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_at_before = filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = ExpenseItem
        fields = [
            'expense',
            'item_name',
            'quantity_min',
            'quantity_max',
            'price_per_item_min',
            'price_per_item_max',
            'total_price_min',
            'total_price_max',
            'created_at_after',
            'created_at_before',
        ]