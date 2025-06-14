from django.db.models import Avg, Sum, F, Subquery, OuterRef, Max
from django_filters import rest_framework as django_filters
from django.db.models import F # Import F

from core.utils.viewsets import DefaultFilterSet, DefaultViewSet
from ..models.invoice.invoice_item import InvoiceItem
from ..serializers import InvoicedItemStatSerializer, ItemNameSerializer # Import ItemNameSerializer


# Filters for InvoicedItemStat
class InvoicedItemStatFilter(DefaultFilterSet):
    item_name = django_filters.CharFilter(field_name='item_name', lookup_expr='icontains')
    start_date = django_filters.DateFilter(field_name='invoice__invoiced_on__date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='invoice__invoiced_on__date', lookup_expr='lte')

    class Meta:
        model = InvoiceItem
        fields = ['item_name', 'start_date', 'end_date']


# ViewSet for InvoicedItemStat
class InvoicedItemStatViewSet(DefaultViewSet):
    queryset = InvoiceItem.objects.all()
    filterset_class = InvoicedItemStatFilter
    ordering_fields = ['item_name', 'average_price', 'last_sold_price', 'total_item_sold']

    if DefaultViewSet.pagination_class:
        DefaultViewSet.pagination_class.page_size = 20

    def get_serializer_class(self):
        if self.request.query_params.get('auto_fill', '').lower() == 'true':
            return ItemNameSerializer
        return InvoicedItemStatSerializer

    def get_queryset(self):
        queryset = InvoiceItem.objects.all()
        if self.request.query_params.get('auto_fill', '').lower() == 'true':
            queryset = queryset.values('item_name').annotate(item_name_alias=F('item_name')).values('item_name_alias').distinct().order_by('item_name_alias').rename_field('item_name_alias', 'item_name')
            # The .values('item_name').distinct() is simpler if only 'item_name' is needed.
            # Using F() and alias to ensure the output field is 'item_name' for ItemNameSerializer
            # A simpler way for distinct names:
            # queryset = queryset.values_list('item_name', flat=True).distinct().order_by('item_name')
            # return [{'item_name': name} for name in queryset] # This would require changing how DRF handles it.
            # So, stick to queryset of dicts:
            queryset = queryset.values('item_name').distinct().order_by('item_name')

        else:
            last_sold_subquery = InvoiceItem.objects.filter(
                item_name=OuterRef('item_name')
            ).order_by('-invoice__invoiced_on', '-created_at').values('price_per_item')[:1]

            queryset = queryset.values('item_name').annotate(
                average_price=Avg('price_per_item'),
                total_item_sold=Sum('quantity'),
                last_sold_price=Subquery(last_sold_subquery)
            ).order_by('item_name')

        return queryset