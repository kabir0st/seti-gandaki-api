from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from core.utils.viewsets import DefaultViewSet

from statements.models.invoice import Invoice, InvoiceItem
from statements.serializers import InvoiceSerializer, InvoiceItemSerializer
from statements.apis.filtersets.invoice import InvoiceFilterSet, InvoiceItemFilterSet


class InvoiceViewSet(DefaultViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['invoice_number', 'customer_name', 'customer_phone_number']
    filterset_class = InvoiceFilterSet


class InvoiceItemViewSet(DefaultViewSet):
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['item_name']
    filterset_class = InvoiceItemFilterSet

    def get_queryset(self):
        invoice_id = self.kwargs.get('invoice_pk')
        if not invoice_id:
            # If no invoice_id is provided in the URL, return an empty queryset
            # or raise an error, depending on desired behavior for non-nested access.
            # For a strictly nested route, this scenario might not even be hit if
            # the URL always enforces invoice_pk.
            return InvoiceItem.objects.none()
        try:
            # Ensure the invoice actually exists
            Invoice.objects.get(pk=invoice_id)
        except Invoice.DoesNotExist:
            raise ValidationError(f"Invoice with id {invoice_id} does not exist.")
        return InvoiceItem.objects.filter(invoice_id=invoice_id)

    def perform_create(self, serializer):
        invoice_id = self.kwargs.get('invoice_pk')
        if not invoice_id:
            raise ValidationError("Invoice ID must be provided in the URL.")
        try:
            invoice = Invoice.objects.get(pk=invoice_id)
        except Invoice.DoesNotExist:
            raise ValidationError(f"Invoice with id {invoice_id} does not exist.")
        serializer.save(invoice=invoice)