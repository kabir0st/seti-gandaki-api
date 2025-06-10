import django_filters
from statements.models.payments import Account


class AccountFilterSet(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Account Name'
    )
    account_number = django_filters.CharFilter(
        field_name='account_number',
        lookup_expr='icontains',
        label='Account Number'
    )
    bank_name = django_filters.CharFilter(
        field_name='bank_name',
        lookup_expr='icontains',
        label='Bank Name'
    )
    branch_name = django_filters.CharFilter(
        field_name='branch_name',
        lookup_expr='icontains',
        label='Branch Name'
    )
    min_amount = django_filters.NumberFilter(
        field_name="current_amount", 
        lookup_expr='gte',
        label='Minimum Amount'
    )
    max_amount = django_filters.NumberFilter(
        field_name="current_amount", 
        lookup_expr='lte',
        label='Maximum Amount'
    )
    
    # Date range filtering
    created_after = django_filters.DateFilter(
        field_name="created_at", 
        lookup_expr='gte', 
        label='Created After (YYYY-MM-DD)'
    )
    created_before = django_filters.DateFilter(
        field_name="created_at", 
        lookup_expr='lte', 
        label='Created Before (YYYY-MM-DD)'
    )

    class Meta:
        model = Account
        fields = [
            'name',
            'account_number',
            'bank_name',
            'branch_name',
            'min_amount',
            'max_amount',
            'created_after',
            'created_before',
        ]