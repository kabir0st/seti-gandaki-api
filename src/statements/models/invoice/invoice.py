from decimal import Decimal

from django.db import models
from django.db.models import signals
from core.utils.functions import to_decimal
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.timezone import now

from core.utils.models import DefaultModel
from statements.models.business import Business
from statements.models.settings import StatementSettings
from statements.utils.generator import generate_invoice_number
from system.models import UserBase
from django.db import models


class InvoiceStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    APPROVED = 'approved', 'Approved'
    SHIPPED = 'shipped', 'Shipped'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class Invoice(DefaultModel):
    # logs and tracking
    created_by = models.ForeignKey(UserBase,
                                   on_delete=models.PROTECT,
                                   related_name='invoices',
                                   blank=True,
                                   null=True)
    last_updated_by = models.ForeignKey(UserBase,
                                        on_delete=models.PROTECT,
                                        null=True,
                                        blank=True,
                                        related_name='last_updated_invoices')
    cancelled_by = models.ForeignKey(UserBase,
                                     on_delete=models.PROTECT,
                                     related_name='cancelled_invoices',
                                     blank=True,
                                     null=True)

    # Customer Info
    customer = models.ForeignKey(Business,
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 blank=True,
                                 related_name='invoices')

    customer_name = models.CharField(max_length=255, null=True, blank=True)
    customer_phone_number = models.CharField(max_length=255, null=True, blank=True)
    customer_pan = models.CharField(max_length=255, null=True, blank=True)

    # invoice details
    invoiced_on = models.DateTimeField(default=now)
    due_on = models.DateTimeField(null=True, blank=True)
    invoice_number = models.CharField(max_length=255,
                                      default=None,
                                      blank=True,
                                      null=True)

    status = models.CharField(max_length=20,
                              choices=InvoiceStatus.choices,
                              default=InvoiceStatus.DRAFT)

    # fields for exporting items

    # Delivery
    delivery_charge = models.DecimalField(default=0.00,
                                          max_digits=60,
                                          decimal_places=2)
    delivery_location = models.TextField(null=True, blank=True)
    delivery_note = models.TextField(null=True, blank=True)
    tracking_code = models.TextField(null=True, blank=True)

    weight_unit = models.CharField(max_length=25, default='cubic_meter',)
    total_weight = models.DecimalField(default=0.00,
                                       max_digits=60,
                                       decimal_places=2)

    # Extra charges and discounts
    additional_charge_amount = models.DecimalField(default=0.00,
                                                   max_digits=60,
                                                   decimal_places=2)
    additional_charge_note = models.TextField(null=True, blank=True)

    additional_discount_amount = models.DecimalField(default=0.00,
                                                     max_digits=60,
                                                     decimal_places=2)
    additional_discount_note = models.TextField(null=True, blank=True)

    # auto update

    sub_total_amount = models.DecimalField(default=0.00,
                                           max_digits=60,
                                           decimal_places=2)

    total_discount_amount = models.DecimalField(default=0.00,
                                                max_digits=60,
                                                decimal_places=2)

    total_taxable_amount = models.DecimalField(default=0.00,
                                               max_digits=60,
                                               decimal_places=2)
    total_tax_amount = models.DecimalField(default=0.00,
                                           max_digits=60,
                                           decimal_places=2)

    bill_amount = models.DecimalField(default=0.00,
                                      max_digits=60,
                                      decimal_places=2)

    paid_amount = models.DecimalField(default=0.00,
                                      max_digits=60,
                                      decimal_places=2)

    serial = models.PositiveIntegerField(default=0)
    fiscal_year_ad = models.CharField(default='',
                                      max_length=6,
                                      null=True,
                                      blank=True)
    fiscal_year_bs = models.CharField(default='',
                                      max_length=6,
                                      null=True,
                                      blank=True)

    is_paid = models.BooleanField(default=False)

    remarks = models.TextField(null=True, blank=True)
    is_taxable = models.BooleanField(default=True)
    ALLOW_UPDATE = [
        'invoiced_on', 'update_discount_service', 'last_updated_by', 'due_on',
        'delivery_location', 'delivery_note', 'tracking_code', 'weight_unit',
        'total_weight', 'count_revision', 'count_bill_printed',
        'last_printed_by', 'last_printed_on', 'is_paid',
        'is_sold_synced_with_ird', 'is_returned_synced_with_ird', 'remarks',
        'serial', 'updated_at', 'last_printed_by_id', 'is_taxable'
    ]

    def save(self, *args, **kwargs):
        self.trigger_value = None
        super(Invoice, self).save(*args, **kwargs)

    def __str__(self):
        if self.customer:
            return (f'{self.customer.full_name}'
                    f' {self.invoice_number or "Draft"}')
        return f'{self.customer_name or ""} {self.invoice_number or "Draft"}'


    @property
    def is_paid_partially(self):
        if self.paid_amount > 0 and self.paid_amount < self.bill_amount:
            return True
        return False




@receiver(pre_save, sender=Invoice)
def pre_save_handler_invoice(sender, instance, **kwargs):
    pass

@receiver(post_save, sender=Invoice)
def post_save_handler_invoice(sender, instance, *args, **kwargs):
    print('  aayo ta invoice ? ', instance.trigger_value)
    if not instance.invoice_number and instance.status in [
            InvoiceStatus.APPROVED, InvoiceStatus.SHIPPED,
            InvoiceStatus.COMPLETED
    ]:
        x = generate_invoice_number(instance, instance.is_taxable)
        instance.invoice_number = x[0]
        instance.fiscal_year_ad = x[1]['ad']
        instance.fiscal_year_bs = x[1]['bs']
        instance.serial = x[2]

    instance.sub_total_amount = Decimal('0.00')
    instance.total_discount_amount = Decimal('0.00')

    instance.paid_amount = Decimal('0.00')

    for invoice_item in instance.invoice_items.filter():
        instance.total_discount_amount += invoice_item.discount_amount
        instance.sub_total_amount += invoice_item.sub_total_amount

    instance.total_discount_amount += to_decimal(
        instance.additional_discount_amount)

    settings = StatementSettings.load()

    instance.bill_amount = to_decimal(instance.sub_total_amount) - \
        to_decimal(instance.total_discount_amount)

    if instance.is_taxable:
        instance.total_taxable_amount = instance.bill_amount
        instance.total_tax_amount = instance.bill_amount * Decimal('0.13')
        instance.bill_amount += instance.total_tax_amount
    else:
        instance.total_taxable_amount = Decimal('0.00')
        instance.total_tax_amount = Decimal('0.00')

    # update paid amount here
    for payment in instance.payments.filter(is_refunded=False,
                                            is_credit_paid=False):
        instance.paid_amount += payment.amount
    instance.is_paid = instance.bill_amount <= instance.paid_amount
    # Trigger rollback if status is CANCELLED
    invoice_pure_save(instance)


def invoice_pure_save(instance):
    signals.post_save.disconnect(post_save_handler_invoice, sender=Invoice)
    signals.pre_save.disconnect(pre_save_handler_invoice, sender=Invoice)
    instance.save()
    signals.post_save.connect(post_save_handler_invoice, sender=Invoice)
    signals.pre_save.connect(pre_save_handler_invoice, sender=Invoice)
