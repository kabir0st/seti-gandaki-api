from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from statements.models import Invoice, PurchaseBill, Expense, Payment


@receiver(post_save, sender=Invoice)
def update_business_on_invoice_change(sender, instance, **kwargs):
    """
    Update business financial totals when invoice is created or updated
    """
    if instance.customer:
        instance.customer.update_financial_totals()


@receiver(post_delete, sender=Invoice)
def update_business_on_invoice_delete(sender, instance, **kwargs):
    """
    Update business financial totals when invoice is deleted
    """
    if instance.customer:
        instance.customer.update_financial_totals()


@receiver(post_save, sender=PurchaseBill)
def update_business_on_purchase_bill_change(sender, instance, **kwargs):
    """
    Update business financial totals when purchase bill is created or updated
    """
    if instance.from_business:
        instance.from_business.update_financial_totals()


@receiver(post_delete, sender=PurchaseBill)
def update_business_on_purchase_bill_delete(sender, instance, **kwargs):
    """
    Update business financial totals when purchase bill is deleted
    """
    if instance.from_business:
        instance.from_business.update_financial_totals()


@receiver(post_save, sender=Expense)
def update_business_on_expense_change(sender, instance, **kwargs):
    """
    Update business financial totals when expense is created or updated
    Note: Currently expenses are not directly linked to businesses,
    but this signal is here for future compatibility
    """
    pass


@receiver(post_delete, sender=Expense)
def update_business_on_expense_delete(sender, instance, **kwargs):
    """
    Update business financial totals when expense is deleted
    Note: Currently expenses are not directly linked to businesses,
    but this signal is here for future compatibility
    """
    pass


@receiver(post_save, sender=Payment)
def update_business_on_payment_change(sender, instance, **kwargs):
    """
    Update business financial totals when payment is created or updated
    """
    if instance.invoice and instance.invoice.customer:
        instance.invoice.customer.update_financial_totals()
    elif instance.purchase_bill and instance.purchase_bill.from_business:
        instance.purchase_bill.from_business.update_financial_totals()
    # Note: expense payments don't affect business totals directly in current model


@receiver(post_delete, sender=Payment)
def update_business_on_payment_delete(sender, instance, **kwargs):
    """
    Update business financial totals when payment is deleted
    """
    if instance.invoice and instance.invoice.customer:
        instance.invoice.customer.update_financial_totals()
    elif instance.purchase_bill and instance.purchase_bill.from_business:
        instance.purchase_bill.from_business.update_financial_totals()
    # Note: expense payments don't affect business totals directly in current model 