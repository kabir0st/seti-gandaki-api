from decimal import Decimal

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from core.utils.models import DefaultModel
from statements.models.business import Business
from system.models.user import UserBase


class BusinessCreditLog(DefaultModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='credit_logs')
    ACTION_CHOICES = (('deposit', 'Deposit'), ('withdraw', 'Withdraw'))
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    amount = models.DecimalField(max_digits=60, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)
    receipt = models.FileField(upload_to='business_credit_receipts', null=True, blank=True)
    created_by = models.ForeignKey(UserBase, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.action.capitalize()} of {self.amount} for {self.business.name}'

    class Meta:
        ordering = ['-created_at']


@receiver(post_save, sender=BusinessCreditLog)
def update_business_credit_on_save(sender, instance, created, **kwargs):
    if created:
        business = instance.business
        if instance.action == 'deposit':
            business.current_amount += instance.amount
        elif instance.action == 'withdraw':
            business.current_amount -= instance.amount
        business.save()
    else:
        # Handle updates to existing logs - requires fetching original instance
        # This is more complex and might be handled by preventing updates or
        # implementing a more sophisticated reconciliation logic if needed.
        # For simplicity, we'll focus on creation and deletion for now.
        pass


@receiver(post_delete, sender=BusinessCreditLog)
def update_business_credit_on_delete(sender, instance, **kwargs):
    business = instance.business
    if instance.action == 'deposit':
        business.current_amount -= instance.amount
    elif instance.action == 'withdraw':
        business.current_amount += instance.amount
    business.save()