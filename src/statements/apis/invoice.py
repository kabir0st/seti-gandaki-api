from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.utils.viewsets import DefaultViewSet

from statements.models.invoice import Invoice, InvoiceItem
from statements.serializers import InvoiceSerializer, InvoiceItemSerializer


class InvoiceViewSet(DefaultViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['invoice_number', 'customer_name', 'customer_phone']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(last_updated_by=self.request.user)


class InvoiceItemViewSet(DefaultViewSet):
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['description', 'item_name']

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'invoice_pk',
                openapi.IN_PATH,
                description="ID of the Invoice",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'invoice_pk',
                openapi.IN_PATH,
                description="ID of the Invoice",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        invoice_pk = self.kwargs.get('invoice_pk')
        if invoice_pk:
            return InvoiceItem.objects.filter(invoice_id=invoice_pk)
        return InvoiceItem.objects.all()