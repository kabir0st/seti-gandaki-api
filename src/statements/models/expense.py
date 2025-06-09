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
    expense = instance.expense
    aggregation = expense.expense_items.aggregate(total=Sum('total_price'))
    expense.total_amount = aggregation['total'] or Decimal('0.00')
    signals.post_save.disconnect(expense_item_post_save_handler, sender=ExpenseItem)
    expense.save(update_fields=['total_amount'])
    signals.post_save.connect(expense_item_post_save_handler, sender=ExpenseItem)


@receiver(post_delete, sender=ExpenseItem)
def expense_item_post_delete_handler(sender, instance, **kwargs):
    expense = instance.expense
    aggregation = expense.expense_items.aggregate(total=Sum('total_price'))
    new_total_amount = aggregation['total'] or Decimal('0.00')

    if expense.total_amount != new_total_amount:
        expense.total_amount = new_total_amount
        expense.save(update_fields=['total_amount'])



@receiver(pre_save, sender=Expense)
def expense_pre_save_handler(sender, instance, **kwargs):
    if instance.pk:
        original_instance = sender.objects.get(pk=instance.pk)
        # Store original values to check for changes in post_save
        instance._original_is_paid = original_instance.is_paid
        instance._original_status = original_instance.status


        if original_instance.status != ExpenseStatus.DRAFT and instance.status == ExpenseStatus.DRAFT:
            instance.status = original_instance.status
        elif original_instance.status != ExpenseStatus.DRAFT and instance.status != original_instance.status:
            if instance.status not in [ExpenseStatus.COMPLETE, ExpenseStatus.CANCELLED]:
                instance.status = original_instance.status
            for field_name in instance.ALLOW_UPDATE:
                setattr(instance, field_name, getattr(original_instance, field_name))

@receiver(post_save, sender=Expense)
def post_save_handler_expense(sender, instance, created, **kwargs):
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

    # Check if is_paid or status has changed
    is_paid_changed = hasattr(instance, '_original_is_paid') and instance.is_paid != instance._original_is_paid
    status_changed = hasattr(instance, '_original_status') and instance.status != instance._original_status

    if is_paid_changed or status_changed:
        # Update attached fuel tickets
        for item in instance.expense_items.all():
            if item.attached_fuel_tickets.exists():
                if instance.status == ExpenseStatus.CANCELLED:
                    # If expense is cancelled, set is_paid on fuel tickets to False
                    item.attached_fuel_tickets.update(is_paid=False)
                elif is_paid_changed:
                    # If is_paid changed, align fuel ticket is_paid with expense is_paid
                    item.attached_fuel_tickets.update(is_paid=instance.is_paid)


    if needs_save:
        # Disconnect signal to avoid recursion and save
        post_save.disconnect(post_save_handler_expense, sender=Expense)
        instance.save(update_fields=['paid_amount', 'is_paid'])
        post_save.connect(post_save_handler_expense, sender=Expense)

