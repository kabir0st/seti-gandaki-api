from django.db import models, transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .cashcounter import CashCounter

class CashCounterLog(models.Model):
    """
    Model to log changes made to a CashCounter.
    """
    # Constants for denomination values and field names
    DENOMINATIONS = {
        'denomination_1000': 1000,
        'denomination_500': 500,
        'denomination_100': 100,
        'denomination_50': 50,
        'denomination_20': 20,
        'denomination_10': 10,
        'denomination_5': 5,
        'denomination_2': 2,
        'denomination_1': 1,
    }
    
    cash_counter = models.ForeignKey(
        CashCounter,
        on_delete=models.PROTECT,
        related_name='logs',
        help_text="The cash counter being updated by this log."
    )
    denomination_1000 = models.IntegerField(default=0, help_text="Change in 1000 Rupee notes (positive for added, negative for removed)")
    denomination_500 = models.IntegerField(default=0, help_text="Change in 500 Rupee notes")
    denomination_100 = models.IntegerField(default=0, help_text="Change in 100 Rupee notes")
    denomination_50 = models.IntegerField(default=0, help_text="Change in 50 Rupee notes")
    denomination_20 = models.IntegerField(default=0, help_text="Change in 20 Rupee notes")
    denomination_10 = models.IntegerField(default=0, help_text="Change in 10 Rupee notes")
    denomination_5 = models.IntegerField(default=0, help_text="Change in 5 Rupee notes")
    denomination_2 = models.IntegerField(default=0, help_text="Change in 2 Rupee notes")
    denomination_1 = models.IntegerField(default=0, help_text="Change in 1 Rupee notes")
    remarks = models.TextField(
        blank=True,
        help_text="Reason or purpose for this cash counter change."
    )
    pre_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total amount in cash counter before this log was applied."
    )
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total amount in cash counter after this log was applied."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_applied = models.BooleanField(
        default=False,
        help_text="Indicates if the changes in this log have been applied to the cash counter."
    )
    
    class Meta:
        verbose_name = "Cash Counter Log"
        verbose_name_plural = "Cash Counter Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Log for {self.cash_counter.counter_name} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_denomination_changes(self):
        """Returns a dictionary of denomination changes."""
        return {field: getattr(self, field) for field in self.DENOMINATIONS.keys()}
    
    def calculate_total_change(self):
        """Calculate the total monetary change from this log."""
        return sum(
            getattr(self, field) * value 
            for field, value in self.DENOMINATIONS.items()
        )
    
    def validate_sufficient_funds(self, cash_counter):
        """Validate if the cash counter has sufficient denominations for the changes."""
        insufficient_denominations = []
        
        for field in self.DENOMINATIONS.keys():
            current_count = getattr(cash_counter, field)
            change = getattr(self, field)
            
            if current_count + change < 0:
                denomination_value = self.DENOMINATIONS[field]
                insufficient_denominations.append(f"{denomination_value} Rupee")
        
        if insufficient_denominations:
            raise ValidationError(
                f"Insufficient notes in cash counter: {', '.join(insufficient_denominations)}"
            )

@receiver(pre_save, sender=CashCounterLog)
def cash_counter_log_pre_save(sender, instance, **kwargs):
    """
    Signal handler to validate changes and set pre_amount before saving the log.
    """
    if instance.pk is not None:
        raise ValidationError("Cash Counter Logs cannot be modified after creation.")
    
    # Ensure the related cash counter exists
    if not hasattr(instance, 'cash_counter') or instance.cash_counter is None:
        raise ValidationError("Related CashCounter does not exist.")
    
    cash_counter = instance.cash_counter
    
    # Set the pre_amount
    instance.pre_amount = cash_counter.total_amount()
    
    # Validate if the requested changes are possible
    instance.validate_sufficient_funds(cash_counter)

@receiver(post_save, sender=CashCounterLog)
def cash_counter_log_post_save(sender, instance, created, **kwargs):
    """
    Signal handler to apply changes to the CashCounter and set final_amount after saving the log.
    """
    if not created or instance.is_applied:
        return
    
    # Use transaction to ensure atomicity
    with transaction.atomic():
        # Select for update to prevent race conditions
        cash_counter = CashCounter.objects.select_for_update().get(pk=instance.cash_counter.pk)
        
        # Apply denomination changes
        denomination_changes = instance.get_denomination_changes()
        for field, change in denomination_changes.items():
            current_value = getattr(cash_counter, field)
            setattr(cash_counter, field, current_value + change)
        
        cash_counter.save(update_fields=list(denomination_changes.keys()))
        
        # Update log with final amount and applied status
        CashCounterLog.objects.filter(pk=instance.pk).update(
            final_amount=cash_counter.total_amount(),
            is_applied=True
        )