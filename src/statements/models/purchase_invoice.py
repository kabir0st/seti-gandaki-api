from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.core.validators import validate_image_file_extension
from django.db import models
from django.db.models.signals import (post_delete, post_save, pre_delete,
                                      pre_save)
from django.dispatch import receiver
from django.utils.timezone import now

from core.utils.functions import limit_size
from statements.models.business import Business
from statements.models.support import Staff
from django.utils.translation import gettext_lazy as _


class Vehicle(models.Model):

    license_plate = models.CharField(_("License Plate"),
                                     max_length=20,
                                     unique=True)
    primary_staffs = models.ManyToManyField(Staff)
    image = models.ImageField(
        null=True,
        upload_to='vehicles',
        blank=True,
        validators=[limit_size, validate_image_file_extension])

    vehicle_type = models.CharField(max_length=255, null=True, blank=True)
    note = models.TextField(default='', null=True, blank=True)

    is_active = models.BooleanField(_("Is Active"), default=True)

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Vehicle")
        verbose_name_plural = _("Vehicles")
        ordering = ["license_plate"]

    def __str__(self):
        return self.license_plate


class PurchaseBill(models.Model):
    purchase_date = models.DateField()
    from_business = models.ForeignKey(Business,
                                      on_delete=models.CASCADE,
                                      null=True,
                                      blank=True)

    purchase_bill_number = models.CharField(max_length=255,
                                            blank=True,
                                            null=True)

    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    grace_discount = models.DecimalField(max_digits=10,
                                         decimal_places=2,
                                         default=0)

    shipping_and_handling_costs = models.DecimalField(max_digits=10,
                                                      decimal_places=2,
                                                      default=0)

    additional_costs = models.DecimalField(max_digits=10,
                                           decimal_places=2,
                                           default=0)

    additional_costs_remarks = models.TextField(max_length=255,
                                                null=True,
                                                blank=True)

    bill_amount = models.DecimalField(max_digits=10,
                                      decimal_places=2,
                                      default=0)
    paid_amount = models.DecimalField(max_digits=10,
                                      decimal_places=2,
                                      default=0)

    shipping_handling_receipt = models.ImageField(
        null=True,
        upload_to='purchase_bills',
        blank=True,
        validators=[limit_size, validate_image_file_extension])

    STATUS_CHOICES = (('draft', 'draft'), ('approved', 'Approved '),
                      ('shipped', 'Shipped'), ('complete', 'Complete'),
                      ('cancelled', 'Cancelled'))

    status = models.CharField(max_length=12,
                              choices=STATUS_CHOICES,
                              default='draft')

    purchase_receipt = models.ImageField(
        null=True,
        upload_to='purchase_bills',
        blank=True,
        validators=[limit_size, validate_image_file_extension])

    notes = models.TextField(blank=True, null=True)

    bill_started_from = models.DateField(default=now)
    bill_completed_on = models.DateField(null=True, blank=True)

    assigned_vehicles = models.ManyToManyField(Vehicle,
                                               related_name='purchase_bills')
    assigned_staffs = models.ManyToManyField(Staff,
                                             related_name='purchase_bills')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.purchase_bill_number


@receiver(pre_delete, sender=PurchaseBill)
def prevent_delete_if_not_draft(sender, instance, **kwargs):
    if instance.status != 'draft':
        raise ValidationError(
            f"Purchase bill with status '{instance.status}' cannot be deleted."
            "Only draft bills can be deleted.")


class PurchaseItem(models.Model):
    purchase_bill = models.ForeignKey(PurchaseBill,
                                      related_name='purchase_items',
                                      on_delete=models.CASCADE)
    item = models.CharField(max_length=255)
    item_description = models.CharField(max_length=255,
                                        default='',
                                        null=True,
                                        blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measurement = models.CharField(max_length=50,
                                           blank=True,
                                           null=True,
                                           default='cubic meter')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    sub_total = models.DecimalField(max_digits=10, decimal_places=2)

    discount_percentage = models.DecimalField(max_digits=4,
                                              decimal_places=2,
                                              default=0)

    taxable_amount = models.DecimalField(max_digits=10,
                                         decimal_places=2,
                                         default=0)

    tax_percent_applied = models.DecimalField(max_digits=4,
                                              decimal_places=2,
                                              default=0)
    tax_amount = models.DecimalField(max_digits=10,
                                     decimal_places=2,
                                     default=0)

    bill_amount = models.DecimalField(max_digits=10,
                                      decimal_places=2,
                                      default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_description}"


@receiver(pre_save, sender=PurchaseItem)
def calculate_purchase_item_amounts(sender, instance, **kwargs):
    # Ensure all necessary values are Decimal for precision
    quantity = Decimal(instance.quantity)
    unit_price = Decimal(instance.unit_price)
    discount_percentage = Decimal(instance.discount_percentage)
    tax_percent_applied = Decimal(instance.tax_percent_applied)

    # Calculate sub_total before discount
    instance.sub_total = quantity * unit_price

    # Apply discount
    discount_amount = (instance.sub_total *
                       discount_percentage) / Decimal('100')
    instance.bill_amount = instance.sub_total - discount_amount

    instance.taxable_amount = Decimal(0)
    instance.tax_amount = Decimal(0)

    if instance.tax_percent_applied > 0:
        instance.taxable_amount = instance.bill_amount
        instance.tax_amount = instance.taxable_amount * (tax_percent_applied /
                                                         Decimal('100'))
        instance.bill_amount = instance.taxable_amount + instance.tax_amount

    # Round to 2 decimal places
    instance.sub_total = instance.sub_total.quantize(Decimal('0.01'),
                                                     rounding=ROUND_HALF_UP)
    instance.taxable_amount = instance.taxable_amount.quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP)
    instance.tax_amount = instance.tax_amount.quantize(Decimal('0.01'),
                                                       rounding=ROUND_HALF_UP)
    instance.bill_amount = instance.bill_amount.quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP)


def update_purchase_bill_totals(purchase_bill_instance):
    """
    Recalculates and updates the sub_total and bill_amount of a PurchaseBill
    based on its associated PurchaseItems and other costs.
    """
    # Ensure we are working with a saved instance, or at least one with a PK
    if not purchase_bill_instance.pk:
        return  # Cannot update totals for an unsaved bill

    items = purchase_bill_instance.purchase_items.all()

    current_bill_sub_total = items.aggregate(
        total=models.Sum('sub_total'))['total'] or Decimal('0.00')

    current_items_bill_total = items.aggregate(
        total=models.Sum('bill_amount'))['total'] or Decimal('0.00')

    purchase_bill_instance.sub_total = current_bill_sub_total.quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Calculate final bill amount for the PurchaseBill
    # Bill amount = (sum of all item bill_amounts) -
    #  grace_discount + shipping + additional_costs
    total_bill_amount = (
        current_items_bill_total -
        Decimal(purchase_bill_instance.grace_discount) +
        Decimal(purchase_bill_instance.shipping_and_handling_costs) +
        Decimal(purchase_bill_instance.additional_costs))
    purchase_bill_instance.bill_amount = total_bill_amount.quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Use update_fields to prevent recursion if PurchaseBill
    # has its own signals and to be more efficient.
    PurchaseBill.objects.filter(pk=purchase_bill_instance.pk).update(
        sub_total=purchase_bill_instance.sub_total,
        bill_amount=purchase_bill_instance.bill_amount)


@receiver(post_save, sender=PurchaseItem)
def purchase_item_saved(sender, instance, created, **kwargs):
    # Check if purchase_bill exists, especially important if it's a new item
    if instance.purchase_bill:
        update_purchase_bill_totals(instance.purchase_bill)


@receiver(post_delete, sender=PurchaseItem)
def purchase_item_deleted(sender, instance, **kwargs):
    # Check if purchase_bill exists
    if instance.purchase_bill:
        update_purchase_bill_totals(instance.purchase_bill)
