from decimal import Decimal

from django.db import models
from django.dispatch import receiver

from core.utils.models import DefaultModel
from statements.models.invoice.invoice import Invoice
from statements.models.purchase_invoice import PurchaseBill
from statements.models.expense import Expense
from statements.models.business import Business
from system.models.user import UserBase
from statements.models.business_credit_log import BusinessCreditLog


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

    payment_method_types = (('business_credit', 'Business Credit'), ('fonepay', 'Fonepay'),
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

    #  from_business_credit
    # if from_business_credit is selected and none of the statements like invoice,
    # purchase_bill or expense are attached
    # Deposit : +  +
    # withdraw : -  -
    # if from_business_credit is selected and any of the statements like invoice,
    # purchase_bill or expense are attached
    # is populated , then related_business must be attached,
    # but related_account must be null.
    # purchase bill pay:
    # related_business: +  
    # invoice pay:
    # related_business: - 
    # expense 
    # related_business: +

    remarks = models.CharField(max_length=255, blank=True, null=True)

    receipt = models.FileField(upload_to='payments', null=True, blank=True)

    is_refunded = models.BooleanField(default=False)

    ACTION_CHOICES = (('withdraw', 'Withdraw'), ('deposit', 'Deposit'))
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, default='deposit')

    def __str__(self):
        return f'{self.amount}'

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.header == 'business_credit':
            if not self.related_business:
                raise ValidationError("Related business must be attached when payment method is 'Business Credit'.")
            
            # Check if any statements are attached
            has_statements = bool(self.invoice or self.purchase_bill or self.expense)
            
            if not has_statements:
                # No statements attached - both business and account required
                if not self.related_account:
                    raise ValidationError("Related account must be attached when no statements are linked to business credit payment.")
                
                # Validation based on action type
                if self.action == 'deposit':
                    # Check if business has enough credit
                    if self.related_business.current_amount < self.amount:
                        raise ValidationError(f"Business '{self.related_business.name}' does not have enough credit. Available: {self.related_business.current_amount}, Required: {self.amount}")
                
                elif self.action == 'withdraw':
                    # Check if account has enough balance
                    if self.related_account.current_amount < self.amount:
                        raise ValidationError(f"Account '{self.related_account.name}' does not have enough balance. Available: {self.related_account.current_amount}, Required: {self.amount}")
            else:
                # Statements attached - account should be null
                if self.related_account:
                    raise ValidationError("Related account must be null when statements are attached to business credit payment.")

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
        instance._original_related_business = original_instance.related_business
        instance._original_header = original_instance.header


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

    # Handle business credit transfers and account updates
    if instance.header == 'business_credit' and instance.related_business:
        if created:
            # New payment with business credit
            _handle_business_credit_payment(instance, created=True)
        else:
            # Updated payment - handle changes
            _handle_business_credit_payment_update(instance)
    
    elif instance.related_account and instance.header != 'business_credit':
        # Handle regular account payments (non-business credit)
        if created:
            _update_account_balance(instance.related_account, instance.action, instance.amount)
        else:
            _handle_regular_payment_update(instance)

    # Save the related objects to trigger their post_save signals
    if instance.purchase_bill:
        instance.purchase_bill.save()
    if instance.invoice:
        instance.invoice.save()
    if instance.expense:
        instance.expense.save()


def _handle_business_credit_payment(instance, created=True):
    """Handle business credit payment creation according to business requirements"""
    # Check if any statements are attached
    has_statements = bool(instance.invoice or instance.purchase_bill or instance.expense)
    
    if not has_statements:
        # Condition 1: No statements attached - both related_business and related_account needed
        if instance.related_account:
            if instance.action == 'deposit':
                # Add to business current amount and add to attached_account current amount
                _update_business_balance(instance.related_business, 'deposit', instance.amount)
                _update_account_balance(instance.related_account, 'deposit', instance.amount)
            elif instance.action == 'withdraw':
                # Subtract from business current amount and subtract from attached_account current amount
                _update_business_balance(instance.related_business, 'withdraw', instance.amount)
                _update_account_balance(instance.related_account, 'withdraw', instance.amount)
            
            # Create business credit log
            _create_business_credit_log(instance)
    else:
        # Condition 2: Statements attached - handle based on statement type
        if instance.purchase_bill:
            # Purchase bill: add to business credit
            _update_business_balance(instance.related_business, 'deposit', instance.amount)
        elif instance.invoice:
            # Invoice pay: subtract from business credit
            _update_business_balance(instance.related_business, 'withdraw', instance.amount)
        elif instance.expense:
            # Expense: add to current amount
            _update_business_balance(instance.related_business, 'deposit', instance.amount)
        
        # Create business credit log
        _create_business_credit_log(instance)


def _handle_business_credit_payment_update(instance):
    """Handle updates to business credit payments"""
    # Check what changed
    amount_changed = hasattr(instance, '_original_amount') and instance.amount != instance._original_amount
    action_changed = hasattr(instance, '_original_action') and instance.action != instance._original_action
    business_changed = hasattr(instance, '_original_related_business') and instance.related_business != instance._original_related_business
    account_changed = hasattr(instance, '_original_related_account') and instance.related_account != instance._original_related_account
    header_changed = hasattr(instance, '_original_header') and instance.header != instance._original_header
    
    if amount_changed or action_changed or business_changed or account_changed or header_changed:
        # Revert the original transaction
        if hasattr(instance, '_original_header') and instance._original_header == 'business_credit':
            _revert_business_credit_payment(instance)
        elif hasattr(instance, '_original_related_account') and instance._original_related_account:
            _revert_account_payment(instance)
        
        # Apply the new transaction
        if instance.header == 'business_credit':
            _handle_business_credit_payment(instance, created=False)
        elif instance.related_account:
            _update_account_balance(instance.related_account, instance.action, instance.amount)


def _revert_business_credit_payment(instance):
    """Revert a business credit payment"""
    if hasattr(instance, '_original_action') and hasattr(instance, '_original_amount'):
        original_action = instance._original_action
        original_amount = instance._original_amount
        original_business = getattr(instance, '_original_related_business', None)
        original_account = getattr(instance, '_original_related_account', None)
        
        # Check if original payment had statements
        has_original_statements = bool(instance.invoice or instance.purchase_bill or instance.expense)
        
        if original_business and original_amount:
            if not has_original_statements and original_account:
                # Original was without statements - reverse both business and account
                if original_action == 'deposit':
                    reverse_business_action = 'withdraw'  # Reverse deposit with withdraw
                    reverse_account_action = 'withdraw'   # Reverse deposit with withdraw
                else:  # withdraw
                    reverse_business_action = 'deposit'   # Reverse withdraw with deposit
                    reverse_account_action = 'deposit'    # Reverse withdraw with deposit
                
                _update_business_balance(original_business, reverse_business_action, original_amount)
                _update_account_balance(original_account, reverse_account_action, original_amount)
            else:
                # Original had statements - reverse business balance based on statement type
                if instance.purchase_bill:
                    reverse_business_action = 'withdraw'  # Reverse deposit
                elif instance.invoice:
                    reverse_business_action = 'deposit'   # Reverse withdraw
                elif instance.expense:
                    reverse_business_action = 'withdraw'  # Reverse deposit
                else:
                    # Fallback to opposite of original action
                    reverse_business_action = 'withdraw' if original_action == 'deposit' else 'deposit'
                
                _update_business_balance(original_business, reverse_business_action, original_amount)


def _revert_account_payment(instance):
    """Revert a regular account payment"""
    if hasattr(instance, '_original_action') and hasattr(instance, '_original_amount'):
        original_action = instance._original_action
        original_amount = instance._original_amount
        original_account = getattr(instance, '_original_related_account', None)
        
        if original_account and original_amount:
            # Reverse the account balance
            if original_action == 'deposit':
                reverse_action = 'withdraw'
            else:  # withdraw
                reverse_action = 'deposit'
            
            _update_account_balance(original_account, reverse_action, original_amount)


def _handle_regular_payment_update(instance):
    """Handle updates to regular (non-business credit) payments"""
    amount_changed = hasattr(instance, '_original_amount') and instance.amount != instance._original_amount
    action_changed = hasattr(instance, '_original_action') and instance.action != instance._original_action
    account_changed = hasattr(instance, '_original_related_account') and instance.related_account != instance._original_related_account
    
    if amount_changed or action_changed or account_changed:
        # Revert original impact
        _revert_account_payment(instance)
        
        # Apply new impact
        _update_account_balance(instance.related_account, instance.action, instance.amount)


def _update_account_balance(account, action, amount):
    """Update account balance based on action"""
    if action == 'deposit':
        account.current_amount += amount
    elif action == 'withdraw':
        account.current_amount -= amount
    account.save()


def _update_business_balance(business, action, amount):
    """Update business balance based on action"""
    if action == 'deposit':
        business.current_amount += amount
    elif action == 'withdraw':
        business.current_amount -= amount
    business.save()


def _create_business_credit_log(payment_instance):
    """Create a business credit log entry for the payment"""
    # Determine the action for the business credit log based on payment context
    has_statements = bool(payment_instance.invoice or payment_instance.purchase_bill or payment_instance.expense)
    
    if not has_statements:
        # No statements - use the payment action directly
        log_action = payment_instance.action
    else:
        # With statements - determine action based on statement type
        if payment_instance.purchase_bill:
            log_action = 'deposit'  # Purchase bill adds to business credit
        elif payment_instance.invoice:
            log_action = 'withdraw'  # Invoice payment subtracts from business credit
        elif payment_instance.expense:
            log_action = 'deposit'  # Expense adds to current amount
        else:
            log_action = payment_instance.action
    
    BusinessCreditLog.objects.create(
        business=payment_instance.related_business,
        action=log_action,
        amount=payment_instance.amount,
        remarks=f"Payment #{payment_instance.id} - {payment_instance.remarks or 'No remarks'}",
        created_by=payment_instance.created_by
    )


@receiver(models.signals.post_delete, sender=Payment)
def post_delete_handler_payment(sender, instance, **kwargs):
    """Handle payment deletion by reversing its effects"""
    if instance.header == 'business_credit' and instance.related_business:
        # Reverse business credit payment
        has_statements = bool(instance.invoice or instance.purchase_bill or instance.expense)
        
        if not has_statements and instance.related_account:
            # No statements - reverse both business and account
            if instance.action == 'deposit':
                reverse_business_action = 'withdraw'
                reverse_account_action = 'withdraw'
            else:  # withdraw
                reverse_business_action = 'deposit'
                reverse_account_action = 'deposit'
            
            _update_business_balance(instance.related_business, reverse_business_action, instance.amount)
            _update_account_balance(instance.related_account, reverse_account_action, instance.amount)
        else:
            # With statements - reverse business balance based on statement type
            if instance.purchase_bill:
                reverse_business_action = 'withdraw'  # Reverse deposit
            elif instance.invoice:
                reverse_business_action = 'deposit'   # Reverse withdraw
            elif instance.expense:
                reverse_business_action = 'withdraw'  # Reverse deposit
            else:
                # Fallback
                reverse_business_action = 'withdraw' if instance.action == 'deposit' else 'deposit'
            
            _update_business_balance(instance.related_business, reverse_business_action, instance.amount)
    
    elif instance.related_account and instance.header != 'business_credit':
        # Reverse regular account payment
        if instance.action == 'deposit':
            reverse_action = 'withdraw'
        else:  # withdraw
            reverse_action = 'deposit'
        
        _update_account_balance(instance.related_account, reverse_action, instance.amount)
