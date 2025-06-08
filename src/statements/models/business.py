from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Business(models.Model):
    name = models.CharField(_("Business Name"), max_length=255)
    registration_number = models.CharField(_("Registration Number"),
                                           max_length=100,
                                           unique=True,
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
    
    # Financial tracking fields
    total_invoice_amount = models.DecimalField(
        _("Total Invoice Amount"), 
        max_digits=60, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    due_invoice_amount = models.DecimalField(
        _("Due Invoice Amount"), 
        max_digits=60, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    total_purchase_bill_amount = models.DecimalField(
        _("Total Purchase Bill Amount"), 
        max_digits=60, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    due_purchase_bill_amount = models.DecimalField(
        _("Due Purchase Bill Amount"), 
        max_digits=60, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    total_expense_amount = models.DecimalField(
        _("Total Expense Amount"), 
        max_digits=60, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    due_expense_amount = models.DecimalField(
        _("Due Expense Amount"), 
        max_digits=60, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    

    class Meta:
        verbose_name = _("Business")
        verbose_name_plural = _("Businesses")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def update_financial_totals(self):
        """
        Calculate and update financial totals from related statements
        """
        # Invoice totals (for customers - invoices sent to this business)
        invoice_totals = self.invoices.aggregate(
            total_amount=Sum('bill_amount'),
            total_paid=Sum('paid_amount')
        )
        self.total_invoice_amount = invoice_totals['total_amount'] or Decimal('0.00')
        invoice_paid = invoice_totals['total_paid'] or Decimal('0.00')
        self.due_invoice_amount = self.total_invoice_amount - invoice_paid

        # Purchase bill totals (for suppliers - bills from this business)
        purchase_totals = self.purchasebill_set.aggregate(
            total_amount=Sum('bill_amount'),
            total_paid=Sum('paid_amount')
        )
        self.total_purchase_bill_amount = purchase_totals['total_amount'] or Decimal('0.00')
        purchase_paid = purchase_totals['total_paid'] or Decimal('0.00')
        self.due_purchase_bill_amount = self.total_purchase_bill_amount - purchase_paid

        # Note: Expenses are not directly related to Business in the current model structure
        # If needed, this would require adding a business field to Expense model
        # For now, setting to zero
        self.total_expense_amount = Decimal('0.00')
        self.due_expense_amount = Decimal('0.00')

        # Save without triggering signals to avoid recursion
        Business.objects.filter(pk=self.pk).update(
            total_invoice_amount=self.total_invoice_amount,
            due_invoice_amount=self.due_invoice_amount,
            total_purchase_bill_amount=self.total_purchase_bill_amount,
            due_purchase_bill_amount=self.due_purchase_bill_amount,
            total_expense_amount=self.total_expense_amount,
            due_expense_amount=self.due_expense_amount
        )


@receiver(post_save, sender=Business)
def business_post_save_handler(sender, instance, created, **kwargs):
    """
    Update financial totals when Business is saved
    """
    if not created:  # Only update for existing businesses
        instance.update_financial_totals()

