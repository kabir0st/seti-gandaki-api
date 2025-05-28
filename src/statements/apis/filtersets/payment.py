import django_filters
from statements.models.payments import Payment
from statements.models.invoice.invoice import Invoice
from statements.models.purchase_invoice import PurchaseBill
from statements.models.expense import Expense


class PaymentFilterSet(django_filters.FilterSet):
    invoice = django_filters.ModelChoiceFilter(
        queryset=Invoice.objects.all(),
        field_name='invoice',
        label='Invoice ID'
    )
    purchase_bill = django_filters.ModelChoiceFilter(
        queryset=PurchaseBill.objects.all(),
        field_name='purchase_bill',
        label='Purchase Bill ID'
    )
    expense = django_filters.ModelChoiceFilter(
        queryset=Expense.objects.all(),
        field_name='expense',
        label='Expense ID'
    )
    created_by = django_filters.CharFilter(
        field_name='created_by__username',  # Assuming UserBase has a username field
        lookup_expr='icontains',
        label='Created By (Username)'
    )
    payment_method = django_filters.ChoiceFilter(
        choices=Payment.payment_method_types,
        field_name='header',
        label='Payment Method'
    )
    min_amount = django_filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name="amount", lookup_expr='lte')
    is_refunded = django_filters.BooleanFilter(field_name='is_refunded')

    class Meta:
        model = Payment
        fields = [
            'invoice',
            'purchase_bill',
            'expense',
            'created_by',
            'payment_method',
            'min_amount',
            'max_amount',
            'is_refunded',
            'created_at', # For date range filtering
            'updated_at', # For date range filtering
        ]

    # Example for date range filtering if needed:
    # start_date = django_filters.DateFilter(field_name="created_at", lookup_expr='gte', label='Start Date (YYYY-MM-DD)')
    # end_date = django_filters.DateFilter(field_name="created_at", lookup_expr='lte', label='End Date (YYYY-MM-DD)')