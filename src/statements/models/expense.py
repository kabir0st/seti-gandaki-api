from decimal import Decimal

from django.db import models
from django.db.models import Sum # Import Sum
from core.utils.functions import limit_size, to_decimal
from django.db.models import signals
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import now
from django.core.validators import validate_image_file_extension

from core.utils.models import DefaultModel
from system.models import UserBase


class ExpenseStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    COMPLETE = 'complete', 'Complete'
    CANCELLED = 'cancelled', 'Cancelled'


class ExpenseCategory(DefaultModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Expense(DefaultModel):
    created_by = models.ForeignKey(UserBase,
                                   on_delete=models.PROTECT,
                                   related_name='expenses_created',
                                   blank=True,
                                   null=True)
    last_updated_by = models.ForeignKey(UserBase,
                                        on_delete=models.PROTECT,
                                        null=True,
                                        blank=True,
                                        related_name='expenses_last_updated')
    cancelled_by = models.ForeignKey(UserBase,
                                     on_delete=models.PROTECT,
                                     related_name='expenses_cancelled',
                                     blank=True,
                                     null=True)

    category = models.ForeignKey(ExpenseCategory,
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 blank=True,
                                 related_name='expenses')

    receipt = models.ImageField(
        null=True,
        upload_to='expenses',
        blank=True,
        validators=[limit_size, validate_image_file_extension])
    paid_to = models.CharField(max_length=255, blank=True, null=True)
    bill_number = models.CharField(max_length=255, blank=True, null=True)
    payment_date = models.DateTimeField(default=now)

    total_amount = models.DecimalField(default=0.00,
                                       max_digits=60,
                                       decimal_places=2)

    status = models.CharField(max_length=20,
                              choices=ExpenseStatus.choices,
                              default=ExpenseStatus.DRAFT)

    remarks = models.TextField(blank=True, null=True)

    paid_amount = models.DecimalField(default=0.00,
                                        max_digits=60,
                                        decimal_places=2)
    is_paid = models.BooleanField(default=False)

    ALLOW_UPDATE = [
        'last_updated_by', 'remarks', 'paid_to', 'bill_number', 'payment_date', 'paid_amount', 'is_paid',
        'category'
    ]

    def __str__(self):
        return f'Expense #{self.id} - {self.category.name if self.category else "N/A"}'


class ExpenseItem(DefaultModel):
    expense = models.ForeignKey(Expense,
                                on_delete=models.CASCADE,
                                related_name='expense_items')

    item_name = models.CharField(max_length=255)
    quantity = models.DecimalField(default=1.00, max_digits=60, decimal_places=2)
    price_per_item = models.DecimalField(default=0.00, max_digits=60, decimal_places=2)
    total_price = models.DecimalField(default=0.00, max_digits=60, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)
    attached_fuel_tickets = models.ManyToManyField('hrm.FuelTicket',related_name='expense_item', blank=True)
    def __str__(self):
        return f'{self.item_name} - {self.expense}'

    def save(self, *args, **kwargs):
        self.total_price = to_decimal(self.quantity) * to_decimal(self.price_per_item)
        super().save(*args, **kwargs)


@receiver(post_save, sender=ExpenseItem)
def expense_item_post_save_handler(sender, created, instance, **kwargs):
    # Update the total_amount of the parent Expense using aggregation
    expense = instance.expense
    aggregation = expense.expense_items.aggregate(total=Sum('total_price'))
    expense.total_amount = aggregation['total'] or Decimal('0.00')
    
    # Disconnect this signal to prevent recursion if expense.save() triggers it.
    # The Expense model's own post_save (post_save_handler_expense) will handle
    # paid_amount and is_paid updates.

    if hasattr(instance, 'attached_fuel_tickets'):
        # If attached_fuel_tickets is a ManyToManyField, ensure it's saved first
        pass

    signals.post_save.disconnect(expense_item_post_save_handler, sender=ExpenseItem)
    expense.save(update_fields=['total_amount']) # Only update total_amount here
    # Reconnect the signal
    signals.post_save.connect(expense_item_post_save_handler, sender=ExpenseItem)


@receiver(post_delete, sender=ExpenseItem)
def expense_item_post_delete_handler(sender, instance, **kwargs):
    # Update the total_amount of the parent Expense after an item is deleted using aggregation
    expense = instance.expense
    # Ensure expense instance is up-to-date if other operations might have changed it
    # expense.refresh_from_db() # Consider if necessary based on broader application logic
    
    aggregation = expense.expense_items.aggregate(total=Sum('total_price'))
    new_total_amount = aggregation['total'] or Decimal('0.00')

    if expense.total_amount != new_total_amount:
        expense.total_amount = new_total_amount
        # Disconnect the ExpenseItem post_save signal temporarily if it's the same handler,
        # though for post_delete, this specific handler (expense_item_post_save_handler) isn't the one being disconnected.
        # The main concern is if expense.save() would somehow re-trigger operations on ExpenseItem.
        # For clarity, ensure we are only disconnecting the relevant signal if there's a risk of loop.
        # Here, we are in post_delete of ExpenseItem, saving Expense.
        # The Expense's own post_save (post_save_handler_expense) will run.
        expense.save(update_fields=['total_amount'])


@receiver(post_save, sender=Expense)
def post_save_handler_expense(sender, instance, created, **kwargs):
    """
    Updates the paid_amount and is_paid status of an Expense
    after payments are made or total_amount changes.
    """
    # Calculate current paid amount using aggregation
    # Assumes 'payments' is the correct related_name from Payment model to Expense
    paid_aggregation = instance.payments.filter(is_refunded=False).aggregate(total_paid=Sum('amount'))
    current_paid_amount = paid_aggregation['total_paid'] or Decimal("0.00")

    needs_save = False
    if instance.paid_amount != current_paid_amount:
        instance.paid_amount = current_paid_amount
        needs_save = True
    
    # Expense is paid if total_amount > 0 and total_amount <= paid_amount
    new_is_paid_status = instance.total_amount > 0 and instance.total_amount <= instance.paid_amount
    if instance.is_paid != new_is_paid_status:
        instance.is_paid = new_is_paid_status
        needs_save = True

    if needs_save:
        # Disconnect signal to avoid recursion and save
        post_save.disconnect(post_save_handler_expense, sender=Expense)
        instance.save(update_fields=['paid_amount', 'is_paid'])
        post_save.connect(post_save_handler_expense, sender=Expense)


@receiver(pre_save, sender=Expense)
def expense_pre_save_handler(sender, instance, **kwargs):
    # Enforce editability based on status
    if instance.pk:  # Only for existing instances
        original_instance = sender.objects.get(pk=instance.pk)
        if original_instance.status != ExpenseStatus.DRAFT and instance.status == ExpenseStatus.DRAFT:
            # Prevent changing status back to DRAFT from non-DRAFT
            instance.status = original_instance.status
        elif original_instance.status != ExpenseStatus.DRAFT and instance.status != original_instance.status:
            # Allow status change from non-DRAFT to COMPLETE or CANCELLED, but not other field edits
            if instance.status not in [ExpenseStatus.COMPLETE, ExpenseStatus.CANCELLED]:
                instance.status = original_instance.status
            # Revert other fields if not in DRAFT
            for field_name in instance.ALLOW_UPDATE:
                setattr(instance, field_name, getattr(original_instance, field_name))