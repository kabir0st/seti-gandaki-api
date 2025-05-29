from decimal import Decimal

from django.db import models
from django.dispatch import receiver

from core.utils.models import DefaultModel
from statements.models import Invoice, PurchaseBill, Expense
from statements.models.expense import Expense
from system.models.user import UserBase


def image_path(instance, filename):
    return f'payment_receipts/{instance.header}_{instance.pk}_{filename}'


class Payment(DefaultModel):
    created_by = models.ForeignKey(UserBase,
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   blank=True)

    payment_method_types = (('credit', 'Credit'), ('fonepay', 'Fonepay'),
                            ('cash', 'Cash'), ('transfer',
                                               'Transfer'), ('card', 'Card'))

    header = models.CharField(max_length=10,
                              choices=payment_method_types,
                              default='cash')

    invoice = models.ForeignKey(Invoice,
                                on_delete=models.CASCADE,
                                related_name="payments",
                                null=True,
                                blank=True)
    purchase_bill = models.ForeignKey(PurchaseBill,
                                       on_delete=models.CASCADE,
                                       related_name="payments",
                                       null=True,
                                       blank=True)

    expense = models.ForeignKey(Expense,
                                on_delete=models.CASCADE,
                                related_name="payments",
                                null=True,
                                blank=True)


    amount = models.DecimalField(default=Decimal(0.00),
                                 max_digits=60,
                                 decimal_places=2)

    remarks = models.CharField(max_length=255, blank=True, null=True)

    receipt = models.FileField(upload_to='payments', null=True, blank=True)

    is_refunded = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.header} {self.amount}'

    @property
    def payment_for(self):
        if self.invoice:
            return {
                'number': self.invoice.invoice_number,
                'type': 'Invoice',
                'url': f'/statements/invoices/{self.invoice.id}',
                'id': self.invoice.id
            }
        elif self.purchase_bill:
            return {
                'number': self.purchase_bill.purchase_bill_number, # Corrected field
                'type': 'Purchase Bill', # Corrected type
                'url': f'/statements/purchase-bills/{self.purchase_bill.id}', # Corrected URL part
                'id': self.purchase_bill.id
            }
        elif self.expense:
            return {
                'number': self.expense.third_party_invoice_number,
                'type': 'Expenses',
                'url': f'/statements/expenses/{self.expense.id}',
                'id': self.expense.id
            }
        return 'Manual'



@receiver(models.signals.post_save, sender=Payment)
def post_save_handler_payment(sender, instance, created, **kwargs):
    if instance.purchase_bill: # Corrected from purchase_order
        instance.purchase_bill.save()
    if instance.invoice:
        instance.invoice.save()
    if instance.expense:
        instance.expense.save()
