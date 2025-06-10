from django.db import models
from decimal import Decimal
from core.utils.models import DefaultModel
from statements.models.business import Business
from system.models.user import UserBase


class BusinessCreditLog(DefaultModel):
    ACTION_CHOICES = (
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw')
    )
    
    business = models.ForeignKey(Business, 
                               on_delete=models.CASCADE, 
                               related_name='credit_logs')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    amount = models.DecimalField(max_digits=60, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)
    receipt = models.FileField(upload_to='business_credit_receipts', blank=True, null=True)
    created_by = models.ForeignKey(UserBase, 
                                 on_delete=models.SET_NULL, 
                                 null=True, 
                                 blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.business.name} - {self.action} - {self.amount}"