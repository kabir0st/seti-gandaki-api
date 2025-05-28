from decimal import Decimal

from django.db import models
from django.db.models import signals
from django.db.models.signals import (post_save,
                                      post_delete)
from django.dispatch import receiver

from core.utils.functions import to_decimal

from core.utils.models import DefaultModel
from statements.models.invoice.invoice import Invoice


class InvoiceItem(DefaultModel):
    invoice = models.ForeignKey(Invoice,
                                on_delete=models.CASCADE,
                                related_name='invoice_items')

    # Item Info
    item_name = models.CharField(max_length=255, blank=True, default='')
    quantity = models.IntegerField(default=0)
    unit = models.CharField(max_length=50, blank=True, default='cubic_meter')
    # billing infos
    price_per_item = models.DecimalField(default=Decimal(0.00),
                                         max_digits=60,
                                         decimal_places=2)

    # for discount and taxes
    discount_percent = models.DecimalField(default=Decimal(0.00),
                                           max_digits=4,
                                           decimal_places=2)
    discount_remarks = models.CharField(max_length=255, blank=True, null=True)

    # Auto update fields
    sub_total_amount = models.DecimalField(default=Decimal(0.00),
                                           max_digits=60,
                                           decimal_places=2)

    bill_amount = models.DecimalField(default=Decimal(0.00),
                                      max_digits=60,
                                      decimal_places=2)


    is_marked_as_complete = models.BooleanField(default=False)
    ALLOW_UPDATE = [
        'is_marked_as_complete', 'profit_flow', 'trigger_value',
        'trigger_value_invoice'
    ]

    def __str__(self):
        return f'{self.item_name} - {self.invoice}'

    def save(self, *args, **kwargs):
        self.trigger_value = None
        self.trigger_value_invoice = None
        super(InvoiceItem, self).save(*args, **kwargs)

    @property
    def discount_amount(self):
        if self.discount_percent:
            return to_decimal(
                (self.sub_total_amount * self.discount_percent) / to_decimal(100))
        return to_decimal(0.00)




@receiver(post_save, sender=InvoiceItem)
def invoice_item_post_save_handler(sender, created, instance, **kwargs):

    instance.sub_total_amount = to_decimal(
        instance.price_per_item) * instance.quantity

    instance.bill_amount = (instance.sub_total_amount -
                                instance.discount_amount )

    signals.post_save.disconnect(invoice_item_post_save_handler,
                                 sender=InvoiceItem)
    
    instance.save()
    # to recalculate if only invoice item's billing is changed
    if instance.trigger_value_invoice:
        instance.invoice.save()
    signals.post_save.connect(invoice_item_post_save_handler,
                              sender=InvoiceItem)


@receiver(post_delete, sender=InvoiceItem)
def handle_post_delete_invoice(sender, instance, *args, **kwargs):
    instance.invoice.save()

