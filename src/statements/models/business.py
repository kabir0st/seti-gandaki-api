from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Business(models.Model):
    name = models.CharField(_("Business Name"), max_length=255)
    registration_number = models.CharField(_("Registration Number"),
                                           max_length=255,
                                           blank=True,
                                           null=True)
    contact_person = models.CharField(_("Contact Person"),
                                      max_length=255,
                                      blank=True,
                                      null=True)
    contact_email = models.EmailField(_("Contact Email"),
                                      max_length=255,
                                      blank=True,
                                      null=True)
    phone_number = models.CharField(_("Phone Number"),
                                    max_length=255,
                                    blank=True,
                                    null=True)
    address = models.TextField(_("Address"), blank=True, null=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    
    current_amount = models.DecimalField(default=Decimal('0.00'),
                                       max_digits=60,
                                       decimal_places=2,
                                       verbose_name=_("Current Amount"),
                                       editable=False)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    

    class Meta:
        verbose_name = _("Business")
        verbose_name_plural = _("Businesses")
        ordering = ["name"]

    def __str__(self):
        return self.name
    
    def reconcile_from_payments(self):
        """
        Reconcile business current_amount based on all related payments
        Returns the calculated amount and updates the business if different
        """
        from statements.models.payments import Payment
        from django.db.models import Sum, Q
        
        # Get all non-refunded payments related to this business
        business_credit_payments = Payment.objects.filter(
            related_business=self,
            header='business_credit',
            is_refunded=False
        )
        
        calculated_amount = Decimal('0.00')
        
        for payment in business_credit_payments:
            has_statements = bool(payment.invoice or payment.purchase_bill or payment.expense)
            
            if not has_statements:
                # No statements - use payment action directly
                if payment.action == 'deposit':
                    calculated_amount += payment.amount
                elif payment.action == 'withdraw':
                    calculated_amount -= payment.amount
            else:
                # With statements - handle based on statement type
                if payment.purchase_bill:
                    # Purchase bill: add to business credit
                    calculated_amount += payment.amount
                elif payment.invoice:
                    # Invoice pay: subtract from business credit
                    calculated_amount -= payment.amount
                elif payment.expense:
                    # Expense: add to current amount
                    calculated_amount += payment.amount
        
        # Update if different
        if self.current_amount != calculated_amount:
            old_amount = self.current_amount
            self.current_amount = calculated_amount
            self.save(update_fields=['current_amount'])
            return {
                'reconciled': True,
                'old_amount': old_amount,
                'new_amount': calculated_amount,
                'difference': calculated_amount - old_amount
            }
        
        return {
            'reconciled': False,
            'current_amount': calculated_amount,
            'message': 'Amount already correct'
        }
