from decimal import Decimal

from django.db import models
from django.db.models import signals
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.utils.timezone import now

from core.utils.functions import is_different, is_equal
from core.utils.models import DefaultModel
from statements.models.business import Business
from statements.utils.generator import generate_invoice_number
from system.models import UserBase


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

    weight_unit = models.CharField(max_length=25, default='g')
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

    profit_flow = models.DecimalField(default=0.00,
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

    # these can be updated even after Invoice is completed.
    count_revision = models.PositiveIntegerField(default=0)
    count_bill_printed = models.PositiveIntegerField(default=0)

    last_printed_by = models.ForeignKey(UserBase,
                                        on_delete=models.PROTECT,
                                        blank=True,
                                        null=True)
    last_printed_on = models.DateTimeField(null=True, blank=True)

    is_paid = models.BooleanField(default=False)

    is_sold_synced_with_ird = models.BooleanField(default=False)
    is_returned_synced_with_ird = models.BooleanField(default=False)

    remarks = models.TextField(null=True, blank=True)
    ALLOW_UPDATE = [
        'invoiced_on', 'update_discount_service', 'last_updated_by', 'due_on',
        'delivery_location', 'delivery_note', 'tracking_code', 'weight_unit',
        'total_weight', 'count_revision', 'count_bill_printed',
        'last_printed_by', 'last_printed_on', 'is_paid',
        'is_sold_synced_with_ird', 'is_returned_synced_with_ird', 'remarks',
        'serial', 'updated_at', 'last_printed_by_id'
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
    def is_synced_with_ird(self):
        if self.status == InvoiceStatus.CANCELLED:
            return (self.is_sold_synced_with_ird
                    and self.is_returned_synced_with_ird)
        return self.is_sold_synced_with_ird

    @property
    def is_paid_partially(self):
        if self.paid_amount > 0 and self.paid_amount < self.bill_amount:
            return True
        return False

    @property
    def paid_through(self):
        return ', '.join(payment.header for payment in self.payments.filter(
            is_refunded=False, is_credit_paid=False))

    def calculate_taxable_amount(self):
        # all discounts must be subtracted from taxable amount.
        settings = StatementSettings.load()
        total_taxable_amount = 0
        if settings.is_vat_applicable:
            if settings.default_tax_type == 'inclusive':
                for item in self.invoice_items.filter():
                    if item.vat_applicable:
                        bill_amount_contribution_percent = (
                            (Decimal(item.bill_amount) /
                             Decimal(self.sub_total_amount)))
                        addition_discount_gained = (
                            Decimal(self.additional_discount_amount) *
                            Decimal(bill_amount_contribution_percent))

                        item_bill_amount = (item.bill_amount -
                                            addition_discount_gained)
                        taxable_amount = ((100 * (item_bill_amount)) /
                                          (100 + item.tax_percent))
                        total_taxable_amount += taxable_amount
            else:
                for item in self.invoice_items.filter():
                    total_taxable_amount += item.taxable_amount
                total_taxable_amount -= self.additional_discount_amount
            return round(total_taxable_amount, 2)
        return 0

    def calculate_tax_amount(self):
        # This logic is assuming VAT tax is consistent all over the
        # invoice item
        # [which always will be the case as it is set in pre_save function]
        # and it is not possible to have different VAT rates.
        # And once calculation is done and invoice is updated to status True
        # it will not recalculate again.
        settings = StatementSettings.load()
        vat = (self.total_taxable_amount * settings.default_tax_rate) / 100
        return round(vat, 2)

    @property
    def total_item_quantity(self):
        return sum(item.quantity for item in self.invoice_items.all())

    def can_complete_invoice(self):
        if self.customer.is_b2b:
            return True
        attached_payments = 0
        for payment in self.payments.filter(is_active=True, is_refunded=False):
            attached_payments += payment.amount
        return attached_payments == self.bill_amount


@receiver(pre_save, sender=Invoice)
def pre_save_handler_invoice(sender, instance, **kwargs):
    instance.update_discount_service = False
    instance.trigger_value = None

    if instance.id:
        instance.update_discount_service = is_different(
            instance, ['is_paid', 'status'])
        old_instance = Invoice.objects.get(id=instance.id)

        # Check if status has been changed and validate
        if old_instance.status != instance.status:
            # Validate status change similar to purchase order
            validate_invoice_status_change(instance, old_instance.status,
                                           instance.status)
            print('we have status ', instance.status)
            # if status is changed check if it is complete and can be completed
            if instance.status in [
                    InvoiceStatus.SHIPPED, InvoiceStatus.COMPLETED
            ] and not instance.can_complete_invoice():
                raise ValidationError('Payment must be attached to invoice.')

            # assign value of changed status for applying or reverting
            instance.trigger_value = instance.status in [
                InvoiceStatus.APPROVED, InvoiceStatus.SHIPPED,
                InvoiceStatus.COMPLETED
            ]
        print('trigger value : ', instance.trigger_value)
        # if above logic is triggered no need to do anything
        if instance.trigger_value is None:
            # if status is not changed and was always complete or cancelled
            old_is_complete = old_instance.status in [
                InvoiceStatus.APPROVED, InvoiceStatus.SHIPPED,
                InvoiceStatus.COMPLETED
            ]
            # Check old status instead of old_instance.is_cancelled
            if (old_is_complete
                    or old_instance.status == InvoiceStatus.CANCELLED):
                if not is_equal(instance, instance.ALLOW_UPDATE):
                    raise ValidationError(
                        'You cannot update restricted fields of invoice'
                        ' that has been marked as complete or was cancelled.')

            # is now cancelled
            # Check status change to CANCELLED
            if (instance.status == InvoiceStatus.CANCELLED
                    and old_instance.status != InvoiceStatus.CANCELLED
                    and old_instance.status != InvoiceStatus.DRAFT):
                instance.trigger_value = False
            # Check status change from CANCELLED
            elif (instance.status != InvoiceStatus.CANCELLED
                  and old_instance.status == InvoiceStatus.CANCELLED):
                raise ValidationError('Cancelled invoices cannot be reverted.')
    else:
        # For new instances, set status to DRAFT
        if instance.status != InvoiceStatus.DRAFT:
            if not instance.can_complete_invoice():
                raise ValidationError(
                    'Invoice with non-draft status cannot be created'
                    ' without attaching payments.')


@receiver(post_save, sender=Invoice)
def post_save_handler_invoice(sender, instance, *args, **kwargs):
    print('  aayo ta invoice ? ', instance.trigger_value)
    if not instance.invoice_number and instance.status in [
            InvoiceStatus.APPROVED, InvoiceStatus.SHIPPED,
            InvoiceStatus.COMPLETED
    ]:
        x = generate_invoice_number(instance)
        instance.invoice_number = x[0]
        instance.fiscal_year_ad = x[1]['ad']
        instance.fiscal_year_bs = x[1]['bs']
        instance.serial = x[2]

    instance.sub_total_amount = Decimal('0.00')
    instance.total_discount_amount = Decimal('0.00')
    instance.profit_flow = Decimal('0.00')

    instance.paid_amount = Decimal('0.00')

    for invoice_item in instance.invoice_items.filter():
        instance.total_discount_amount += invoice_item.discount_amount
        instance.sub_total_amount += invoice_item.sub_total_amount
        instance.profit_flow += invoice_item.profit_flow

    instance.total_discount_amount += Decimal(
        instance.additional_discount_amount)

    instance.total_taxable_amount = instance.calculate_taxable_amount()
    instance.total_tax_amount = instance.calculate_tax_amount()
    settings = StatementSettings.load()

    instance.bill_amount = Decimal(instance.sub_total_amount) - \
        Decimal(instance.total_discount_amount) + \
        Decimal(instance.delivery_charge) + \
        Decimal(instance.additional_charge_amount)

    if settings.default_tax_type == 'exclusive':
        instance.bill_amount += instance.total_tax_amount

    # final profit
    instance.profit_flow = instance.profit_flow - \
        Decimal(instance.additional_discount_amount)

    # update paid amount here
    for payment in instance.payments.filter(is_refunded=False,
                                            is_credit_paid=False):
        instance.paid_amount += payment.amount
    instance.is_paid = instance.bill_amount <= instance.paid_amount
    # Trigger rollback if status is CANCELLED
    print('we have status ', instance.status, instance.trigger_value)
    if instance.trigger_value is not None:
        if instance.trigger_value:
            from transactions.models.event_listener import \
                create_ledger_entries_for_invoice
            imprint_sales(instance)
            create_ledger_entries_for_invoice(instance)
        else:
            from transactions.models.event_listener import \
                roll_back_ledger_entries_for_invoice
            roll_back_sales(instance)
            roll_back_ledger_entries_for_invoice(instance)
    if (instance.update_discount_service and instance.customer
            and not instance.customer.is_b2b):
        from statements.tasks import update_invoice_in_discount
        # have a delay function here
        update_invoice_in_discount({
            'phone_number': instance.customer.phone_number,
            'invoice_number': instance.invoice_number,
            'bill_amount': instance.bill_amount,
            'profit_flow': instance.profit_flow
        })
    invoice_pure_save(instance)


def imprint_sales(instance):
    print('imprint triggered')
    for invoice_item in instance.invoice_items.all():
        if not invoice_item.is_marked_as_complete:
            invoice_item.is_marked_as_complete = True
            invoice_item.save()


def roll_back_sales(instance):
    print('rollback triggered')
    for invoice_item in instance.invoice_items.all():
        if invoice_item.is_marked_as_complete:
            invoice_item.is_marked_as_complete = False
            invoice_item.save()


def invoice_pure_save(instance):
    signals.post_save.disconnect(post_save_handler_invoice, sender=Invoice)
    signals.pre_save.disconnect(pre_save_handler_invoice, sender=Invoice)
    instance.save()
    signals.post_save.connect(post_save_handler_invoice, sender=Invoice)
    signals.pre_save.connect(pre_save_handler_invoice, sender=Invoice)
