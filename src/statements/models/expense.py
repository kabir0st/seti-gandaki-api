from decimal import Decimal

from django.db import models
from django.db.models import signals
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import now

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

    ALLOW_UPDATE = [
        'last_updated_by', 'remarks', 'paid_to', 'bill_number', 'payment_date',
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

    def __str__(self):
        return f'{self.item_name} - {self.expense}'

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.price_per_item
        super().save(*args, **kwargs)


@receiver(post_save, sender=ExpenseItem)
def expense_item_post_save_handler(sender, created, instance, **kwargs):
    # Update the total_amount of the parent Expense
    expense = instance.expense
    expense.total_amount = sum(item.total_price for item in expense.expense_items.all())
    # Disconnect the signal to prevent recursion when saving the expense
    signals.post_save.disconnect(expense_item_post_save_handler, sender=ExpenseItem)
    expense.save()
    # Reconnect the signal
    signals.post_save.connect(expense_item_post_save_handler, sender=ExpenseItem)


@receiver(post_delete, sender=ExpenseItem)
def expense_item_post_delete_handler(sender, instance, **kwargs):
    # Update the total_amount of the parent Expense after an item is deleted
    expense = instance.expense
    expense.total_amount = sum(item.total_price for item in expense.expense_items.all())
    # Disconnect the signal to prevent recursion when saving the expense
    signals.post_save.disconnect(expense_item_post_save_handler, sender=ExpenseItem)
    expense.save()
    # Reconnect the signal
    signals.post_save.connect(expense_item_post_save_handler, sender=ExpenseItem)


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