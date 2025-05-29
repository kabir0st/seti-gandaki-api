import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from statements.models import Staff

class FoodTicket(models.Model):
    """
    Model to represent a food ticket issued to a staff member.
    """
    MEAL_TYPE_CHOICES = [
        ('breakfast', _('Breakfast')),
        ('lunch', _('Lunch')),
        ('dinner', _('Dinner')),
        ('snack', _('Snack')),
        ('other', _('Other')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name='food_tickets',
        verbose_name=_('Staff Member'),
        help_text=_('The staff member to whom the ticket is issued.')
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='food_tickets_issued',
        verbose_name=_('Issued By'),
        help_text=_('The user who generated this food ticket.')
    )
    ticket_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True, # Will be auto-generated if kept blank
        verbose_name=_('Ticket Number'),
        help_text=_('Unique identifier for the ticket (e.g., FT-0001). Auto-generated if blank.')
    )
    meal_type = models.CharField(
        max_length=50,
        choices=MEAL_TYPE_CHOICES,
        verbose_name=_('Meal Type'),
        help_text=_('Type of meal for which the ticket is valid.')
    )
    issued_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Issued At'),
        help_text=_('Timestamp when the ticket was generated.')
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name=_('Is Used'),
        help_text=_('Indicates if the ticket has been redeemed.')
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Used At'),
        help_text=_('Timestamp when the ticket was redeemed.')
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Notes'),
        help_text=_('Any additional notes or comments.')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _('Food Ticket')
        verbose_name_plural = _('Food Tickets')
        ordering = ['-issued_at']

    def __str__(self):
        staff_name = self.staff.get_full_name() if hasattr(self.staff, 'get_full_name') else str(self.staff)
        return f'{self.ticket_number} for {staff_name} ({self.get_meal_type_display()})'

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate a unique ticket number, e.g., FT-YYYYMMDD-XXXX
            # This is a simple example; a more robust sequence generator might be needed.
            last_ticket = FoodTicket.objects.order_by('id').last()
            if last_ticket and last_ticket.ticket_number and last_ticket.ticket_number.startswith('FT-'):
                try:
                    last_num = int(last_ticket.ticket_number.split('-')[-1])
                    new_num = last_num + 1
                except ValueError:
                    new_num = 1 # Fallback if parsing fails
            else:
                new_num = 1
            self.ticket_number = f'FT-{new_num:04d}' # Example: FT-0001
        super().save(*args, **kwargs)

    # Consider adding a method to mark as used:
    # def mark_as_used(self):
    #     if not self.is_used:
    #         self.is_used = True
    #         self.used_at = timezone.now()
    #         self.save(update_fields=['is_used', 'used_at'])