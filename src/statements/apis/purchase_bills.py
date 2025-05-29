from django_filters import rest_framework as django_filters
from rest_framework.exceptions import ValidationError

from core.utils.viewsets import DefaultFilterSet, DefaultViewSet
from ..models.purchase_invoice import PurchaseBill, PurchaseItem
from ..serializers import (PurchaseBillSerializer,
                           PurchaseItemDetailSerializer,
                           PurchaseItemListSerializer)


# Filters for PurchaseItem
class PurchaseItemFilter(DefaultFilterSet):
    purchase_bill = django_filters.NumberFilter(field_name='purchase_bill__id')
    purchase_bill_number = django_filters.CharFilter(
        field_name='purchase_bill__purchase_bill_number',
        lookup_expr='icontains')
    item = django_filters.CharFilter(field_name='item', lookup_expr='icontains')
    item_description = django_filters.CharFilter(field_name='item_description',
                                          lookup_expr='icontains')
    min_quantity = django_filters.NumberFilter(field_name='quantity',
                                        lookup_expr='gte')
    max_quantity = django_filters.NumberFilter(field_name='quantity',
                                        lookup_expr='lte')
    min_unit_price = django_filters.NumberFilter(field_name='unit_price',
                                          lookup_expr='gte')
    max_unit_price = django_filters.NumberFilter(field_name='unit_price',
                                          lookup_expr='lte')
    min_bill_amount = django_filters.NumberFilter(field_name='bill_amount',
                                           lookup_expr='gte')
    max_bill_amount = django_filters.NumberFilter(field_name='bill_amount',
                                           lookup_expr='lte')

    class Meta:
        model = PurchaseItem
        fields = [
            'unit_of_measurement', 'discount_percentage',
            'tax_percent_applied', 'created_at', 'updated_at'
        ]


# ViewSet for PurchaseItem
class PurchaseItemViewSet(DefaultViewSet):
    queryset = PurchaseItem.objects.select_related('purchase_bill').all()
    filterset_class = PurchaseItemFilter
    search_fields = [
        'item', 'item_description', 'purchase_bill__purchase_bill_number'
    ]
    ordering_fields = [
        'id', 'item', 'quantity', 'unit_price', 'bill_amount', 'created_at',
        'purchase_bill__purchase_bill_number'
    ]  # Includes default ordering fields from DefaultViewSet

    def get_queryset(self):
        queryset = super().get_queryset()
        purchase_bill_id = self.kwargs.get('purchase_bill_pk')
        if purchase_bill_id:
            queryset = queryset.filter(purchase_bill__id=purchase_bill_id)
            return queryset
        # If no purchase_bill_id is provided, raise an error
        return queryset.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseItemListSerializer
        return PurchaseItemDetailSerializer


# Filters for PurchaseBill
class PurchaseBillFilter(DefaultFilterSet):
    from_business_name = django_filters.CharFilter(field_name='from_business__name',
                                            lookup_expr='icontains')
    purchase_bill_number = django_filters.CharFilter(
        field_name='purchase_bill_number', lookup_expr='icontains')
    min_bill_amount = django_filters.NumberFilter(field_name='bill_amount',
                                           lookup_expr='gte')
    max_bill_amount = django_filters.NumberFilter(field_name='bill_amount',
                                           lookup_expr='lte')
    min_paid_amount = django_filters.NumberFilter(field_name='paid_amount',
                                           lookup_expr='gte')
    max_paid_amount = django_filters.NumberFilter(field_name='paid_amount',
                                           lookup_expr='lte')
    purchase_date_after = django_filters.DateFilter(field_name='purchase_date',
                                             lookup_expr='gte')
    purchase_date_before = django_filters.DateFilter(field_name='purchase_date',
                                              lookup_expr='lte')

    class Meta:
        model = PurchaseBill
        fields = [
            'from_business', 'status', 'purchase_date', 'created_at', 'updated_at'
        ]


# ViewSet for PurchaseBill
class PurchaseBillViewSet(DefaultViewSet):
    serializer_class = PurchaseBillSerializer
    filterset_class = PurchaseBillFilter
    search_fields = [
        'purchase_bill_number', 'from_business__name', 'notes',
        'purchase_items__item', 'purchase_items__item_description'
    ]
    ordering_fields = [
        'id', 'purchase_date', 'purchase_bill_number', 'bill_amount',
        'paid_amount', 'status', 'created_at', 'from_business__name'
    ]  # Includes default ordering fields from DefaultViewSet

    def get_queryset(self):
        queryset = PurchaseBill.objects.prefetch_related(
            'purchase_items').select_related('from_business').all()
        return queryset
