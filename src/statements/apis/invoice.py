from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from core.utils.viewsets import DefaultViewSet

from statements.models.invoice import Invoice, InvoiceItem
from statements.serializers import InvoiceSerializer, InvoiceItemSerializer
from statements.apis.filtersets.invoice import (InvoiceFilterSet,
                                                InvoiceItemFilterSet)


class InvoiceViewSet(DefaultViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    search_fields = [
        'invoice_number', 'customer_name', 'customer_phone_number'
    ]
    filterset_class = InvoiceFilterSet

    def export_data(self, request, *args, **kwargs):
        """
        Custom export method that includes invoice item data.
        Each invoice row will include a comma-separated list of item details.
        """
        # Get the filtered queryset
        queryset = self.filter_queryset(self.get_queryset())

        # Prefetch related invoice items to avoid N+1 queries
        queryset = queryset.prefetch_related('invoice_items')

        # Get pagination parameters
        start_param = request.GET.get('start')
        end_param = request.GET.get('end')

        # Only apply pagination if both start and end are provided
        if (start_param is not None and end_param is not None
                and end_param != 'None'):
            try:
                start = int(start_param)
                end = int(end_param)
                queryset = queryset[start:end]
            except (ValueError, TypeError):
                # If invalid pagination parameters, export all data
                pass
        # If no pagination parameters provided, export all data

        # Prepare data for export
        export_data = []

        for invoice in queryset:
            # Get basic invoice data
            invoice_data = {
                'id':
                invoice.id,
                'invoice_number':
                invoice.invoice_number or 'Draft',
                'customer_name':
                invoice.customer_name
                or (invoice.customer.name if invoice.customer else ''),
                'customer_phone_number':
                invoice.customer_phone_number or '',
                'customer_pan':
                invoice.customer_pan or '',
                'invoiced_on':
                invoice.invoiced_on.strftime('%Y-%m-%d %H:%M:%S')
                if invoice.invoiced_on else '',
                'due_on':
                invoice.due_on.strftime('%Y-%m-%d %H:%M:%S')
                if invoice.due_on else '',
                'status':
                invoice.get_status_display(),
                'delivery_charge':
                float(invoice.delivery_charge),
                'delivery_location':
                invoice.delivery_location or '',
                'delivery_note':
                invoice.delivery_note or '',
                'tracking_code':
                invoice.tracking_code or '',
                'weight_unit':
                invoice.weight_unit,
                'total_weight':
                float(invoice.total_weight),
                'additional_charge_amount':
                float(invoice.additional_charge_amount),
                'additional_charge_note':
                invoice.additional_charge_note or '',
                'additional_discount_amount':
                float(invoice.additional_discount_amount),
                'additional_discount_note':
                invoice.additional_discount_note or '',
                'sub_total_amount':
                float(invoice.sub_total_amount),
                'total_discount_amount':
                float(invoice.total_discount_amount),
                'total_taxable_amount':
                float(invoice.total_taxable_amount),
                'total_tax_amount':
                float(invoice.total_tax_amount),
                'bill_amount':
                float(invoice.bill_amount),
                'paid_amount':
                float(invoice.paid_amount),
                'is_paid':
                'Yes' if invoice.is_paid else 'No',
                'remarks':
                invoice.remarks or '',
                'is_taxable':
                'Yes' if invoice.is_taxable else 'No',
                'created_at':
                invoice.created_at.strftime('%Y-%m-%d %H:%M:%S')
                if invoice.created_at else '',
                'updated_at':
                invoice.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                if invoice.updated_at else '',
            }

            # Add created_by info if available
            if invoice.created_by:
                invoice_data['created_by'] = invoice.created_by.get_full_name(
                ) or invoice.created_by.username
            else:
                invoice_data['created_by'] = ''

            # Add last_updated_by info if available
            if invoice.last_updated_by:
                invoice_data[
                    'last_updated_by'] = invoice.last_updated_by.get_full_name(
                    ) or invoice.last_updated_by.username
            else:
                invoice_data['last_updated_by'] = ''

            # Add customer business info if available
            if invoice.customer:
                invoice_data['customer_business'] = invoice.customer.name
            else:
                invoice_data['customer_business'] = ''

            # Prepare invoice items data as comma-separated strings
            item_names = []
            quantities = []
            units = []
            price_per_items = []
            bill_amounts = []

            for item in invoice.invoice_items.all():
                item_names.append(item.item_name or '')
                quantities.append(str(item.quantity))
                units.append(item.unit or '')
                price_per_items.append(str(item.price_per_item))
                bill_amounts.append(str(item.bill_amount))

            # Add comma-separated item data
            invoice_data['item_names'] = ', '.join(item_names)
            invoice_data['quantities'] = ', '.join(quantities)
            invoice_data['units'] = ', '.join(units)
            invoice_data['price_per_items'] = ', '.join(price_per_items)
            invoice_data['item_bill_amounts'] = ', '.join(bill_amounts)
            invoice_data['total_items'] = len(item_names)

            export_data.append(invoice_data)

        return export_data


class InvoiceItemViewSet(DefaultViewSet):
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['item_name']
    filterset_class = InvoiceItemFilterSet

    def get_queryset(self):
        invoice_id = self.kwargs.get('invoice_pk')
        if not invoice_id:
            return InvoiceItem.objects.none()
        try:
            # Ensure the invoice actually exists
            Invoice.objects.get(pk=invoice_id)
        except Invoice.DoesNotExist:
            raise ValidationError(
                f"Invoice with id {invoice_id} does not exist.")
        return InvoiceItem.objects.filter(invoice_id=invoice_id)

    def perform_create(self, serializer):
        invoice_id = self.kwargs.get('invoice_pk')
        if not invoice_id:
            raise ValidationError("Invoice ID must be provided in the URL.")
        try:
            invoice = Invoice.objects.get(pk=invoice_id)
        except Invoice.DoesNotExist:
            raise ValidationError(
                f"Invoice with id {invoice_id} does not exist.")
        serializer.save(invoice=invoice)
