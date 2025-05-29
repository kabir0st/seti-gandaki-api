from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from core.utils.viewsets import DefaultViewSet

from statements.models.invoice import Invoice, InvoiceItem
from statements.serializers import InvoiceSerializer, InvoiceItemSerializer


class InvoiceViewSet(DefaultViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['invoice_number', 'customer_name', 'customer_phone']


class InvoiceItemViewSet(DefaultViewSet):
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsAuthenticated]
    search_fields = [ 'item_name']

    def get_queryset(self):
        invoice_id = self.kwargs.get('invoice_pk')
        if invoice_id:
            return InvoiceItem.objects.filter(invoice_id=invoice_id)
        # If no invoice_id is provided, raise an error
        return InvoiceItem.objects.none()