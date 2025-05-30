from django.db.models import Avg, Sum, F, Subquery, OuterRef # Keep F
from django_filters import rest_framework as django_filters

from core.utils.viewsets import DefaultFilterSet, DefaultViewSet
from ..models.expense import ExpenseItem
from ..serializers import ExpensedItemStatSerializer, ItemNameSerializer # Import ItemNameSerializer


# Filters for ExpensedItemStat
class ExpensedItemStatFilter(DefaultFilterSet):
    item_name = django_filters.CharFilter(field_name='item_name', lookup_expr='icontains')
    start_date = django_filters.DateFilter(field_name='expense__payment_date__date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='expense__payment_date__date', lookup_expr='lte')

    class Meta:
        model = ExpenseItem
        fields = ['item_name', 'start_date', 'end_date']


# ViewSet for ExpensedItemStat
class ExpensedItemStatViewSet(DefaultViewSet):
    filterset_class = ExpensedItemStatFilter
    ordering_fields = ['item_name', 'average_price', 'last_expensed_price', 'total_item_expensed_quantity']

    if DefaultViewSet.pagination_class:
        DefaultViewSet.pagination_class.page_size = 20

    def get_serializer_class(self):
        if self.request.query_params.get('auto_fill', '').lower() == 'true':
            return ItemNameSerializer
        return ExpensedItemStatSerializer

    def get_queryset(self):
        queryset = ExpenseItem.objects.all()

        if self.request.query_params.get('auto_fill', '').lower() == 'true':
            # For auto_fill, we only need distinct item names
            # Filters (item name search, date range) should still apply
            queryset = queryset.values('item_name').distinct().order_by('item_name')
        else:
            # Original aggregation logic
            last_expensed_subquery = ExpenseItem.objects.filter(
                item_name=OuterRef('item_name')
            ).order_by('-expense__payment_date', '-created_at').values('price_per_item')[:1]

            queryset = queryset.values('item_name').annotate(
                average_price=Avg('price_per_item'),
                total_item_expensed_quantity=Sum('quantity'),
                last_expensed_price=Subquery(last_expensed_subquery)
            ).order_by('item_name')

        return queryset