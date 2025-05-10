from django.db import models

from statements.models.business import Business


class SalesInvoice(models.Model):
    invoice_number = models.CharField(max_length=255, unique=True)
    invoice_date = models.DateField()
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    sales_order_number = models.CharField(max_length=255,
                                          blank=True,
                                          null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discounts = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_delivery = models.DecimalField(max_digits=10,
                                            decimal_places=2,
                                            default=0)
    total_amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    payment_terms = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.invoice_number


class SalesInvoiceLineItem(models.Model):
    invoice = models.ForeignKey(SalesInvoice,
                                related_name='line_items',
                                on_delete=models.CASCADE)
    item_description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measurement = models.CharField(max_length=50,
                                           blank=True,
                                           null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_item_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.item_description}"
