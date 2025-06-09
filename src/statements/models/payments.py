from decimal import Decimal

from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ValidationError # Added import

from core.utils.models import DefaultModel
from statements.models import Invoice, PurchaseBill, Expense
from statements.models.business import Business
from statements.models.business_credit_log import BusinessCreditLog # Added import
from statements.models.expense import Expense
from system.models.user import UserBase


def image_path(instance, filename):
    return f'payment_receipts/{instance.pk}_{filename}'


class Account(DefaultModel):
    name = models.CharField(max_length=255, unique=True)
    account_number = models.CharField(max_length=50, unique=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    current_amount = models.DecimalField(default=Decimal('0.00'),
                                        max_digits=60,
                                        decimal_places=2,
                                        verbose_name="Current Amount")

    def __str__(self):
        return f'{self.name} ({self.account_number})'
    
    class Meta:
        verbose_name_plural = "Accounts"

class Payment(DefaultModel):
    created_by = models.ForeignKey(UserBase,
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   blank=True)

    payment_method_types = (('from_business_credit', 'From Business Credit'), ('fonepay', 'Fonepay'),
                            ('cash', 'Cash'), ('transfer',
                                               'Transfer'), ('card', 'Card'))

    header = models.CharField(max_length=20,
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

    related_business = models.ForeignKey(Business, on_delete=models.PROTECT, default=None, null=True, blank=True)
    related_account = models.ForeignKey(Account, on_delete=models.PROTECT, default=None, null=True, blank=True)
    
    remarks = models.CharField(max_length=255, blank=True, null=True)

    receipt = models.FileField(upload_to='payments', null=True, blank=True)

    is_refunded = models.BooleanField(default=False)

    ACTION_CHOICES = (('withdraw', 'Withdraw'), ('deposit', 'Deposit'))
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, default='deposit')

    def __str__(self):
        return f'{self.amount}'

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.header == 'from_business_credit':
            if not self.related_business:
                raise ValidationError("Related business must be attached when payment method is 'From Business Credit'.")

            # Check if business has enough credit
            if self.related_business.current_amount < self.amount:
                raise ValidationError(f"Business '{self.related_business.name}' does not have enough credit.")

            # Create a BusinessCreditLog for the withdrawal
            # This should ideally be done in a post_save signal or a separate service
            # to ensure the Payment is saved successfully first.
            # However, for validation purposes in clean, we only check the amount.
            # The actual log creation and business amount update will be handled
            # in the post_save signal of the Payment model.
            pass # The actual logic for creating the log and updating business amount will be in post_save.

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
                'number': self.expense.bill_number,
                'type': 'Expenses',
                'url': f'/statements/expenses/{self.expense.id}',
                'id': self.expense.id
            }
        return 'Manual'



@receiver(models.signals.pre_save, sender=Payment)
def pre_save_handler_payment(sender, instance, **kwargs):
    if instance.pk:
        original_instance = sender.objects.get(pk=instance.pk)
        instance._original_amount = original_instance.amount
        instance._original_action = original_instance.action
        instance._original_related_account = original_instance.related_account


@receiver(models.signals.post_save, sender=Payment)
def post_save_handler_payment(sender, instance, created, **kwargs):
    # Determine related business based on the linked object
    related_business = None
    if instance.invoice:
        related_business = instance.invoice.customer
    elif instance.purchase_bill:
        related_business = instance.purchase_bill.from_business
    # For expense, there is no direct link to Business in the current schema,
    # so related_business remains None.

    # Check if related_business has changed to avoid infinite recursion
    if instance.related_business != related_business:
        instance.related_business = related_business
        # Disconnect the signal to prevent recursion during the save
        models.signals.post_save.disconnect(post_save_handler_payment, sender=Payment)
        instance.save(update_fields=['related_business'])
        # Reconnect the signal
        models.signals.post_save.connect(post_save_handler_payment, sender=Payment)

    # Update related account amount and create BusinessCreditLog if applicable
    if instance.related_account:
        if instance.header == 'from_business_credit':
            # Business credit is handled by BusinessCreditLog signal
            # Create BusinessCreditLog for withdrawal
            if created or (hasattr(instance, '_original_amount') and (instance.amount != instance._original_amount or instance.related_business != instance._original_related_business)):
                 # If created or amount/business changed, create a new log entry
                 # For updates, find the existing log and update it, or create a new one if not found.
                 if not created:
                    try:
                        # Find the BusinessCreditLog created for the original payment
                        original_log = BusinessCreditLog.objects.get(
                            remarks=f'Payment {instance.id} using business credit',
                            business=instance._original_related_business,
                            action='withdraw',
                            amount=instance._original_amount
                        )
                        # Update the existing log entry
                        original_log.business = instance.related_business
                        original_log.amount = instance.amount
                        original_log.save() # This will trigger the BusinessCreditLog post_save signal
                    except BusinessCreditLog.DoesNotExist:
                        # If the original log doesn't exist (e.g., manual creation or error),
                        # create a new one for the current state.
                         BusinessCreditLog.objects.create(
                            business=instance.related_business,
                            action='withdraw',
                            amount=instance.amount,
                            remarks=f'Payment {instance.id} using business credit',
                            created_by=instance.created_by
                         )
                 else:
                     # For newly created payments with 'from_business_credit'
                     BusinessCreditLog.objects.create(
                        business=instance.related_business,
                        action='withdraw',
                        amount=instance.amount,
                        remarks=f'Payment {instance.id} using business credit',
                        created_by=instance.created_by
                     )


        else:
            # Other payment methods: update account directly
            if created:
                # New payment: update account based on action
                if instance.action == 'deposit':
                    instance.related_account.current_amount += instance.amount
                elif instance.action == 'withdraw':
                    instance.related_account.current_amount -= instance.amount
                instance.related_account.save()
            else:
                # Existing payment: check if amount, action, or related_account changed
                amount_changed = instance.amount != instance._original_amount
                action_changed = instance.action != instance._original_action
                account_changed = instance.related_account != instance._original_related_account

                if amount_changed or action_changed or account_changed:
                    # Revert previous impact on the original account if account changed or action/amount changed
                    if instance._original_related_account:
                        if instance._original_action == 'deposit':
                            instance._original_related_account.current_amount -= instance._original_amount
                        elif instance._original_action == 'withdraw':
                            instance._original_related_account.current_amount += instance._original_amount
                        instance._original_related_account.save()

                    # Apply new impact on the current account
                    if instance.action == 'deposit':
                        instance.related_account.current_amount += instance.amount
                    elif instance.action == 'withdraw':
                        instance.related_account.current_amount -= instance.amount
                    instance.related_account.save()

    # Save the related objects to trigger their post_save signals
    if instance.purchase_bill:
        instance.purchase_bill.save()
    if instance.invoice:
        instance.invoice.save()
    if instance.expense:
        instance.expense.save()
