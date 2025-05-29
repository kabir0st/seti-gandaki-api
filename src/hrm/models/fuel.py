from decimal import Decimal
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator,  RegexValidator

from core.utils.models.abstract import DefaultModel
from core.utils.functions import generate_unique_code # Added import
from statements.models.purchase_invoice import Vehicle


class PetrolStation(DefaultModel):
    name = models.CharField(max_length=255)
    station_code = models.CharField(
        max_length=4,
        unique=True,
        validators=[RegexValidator(r'^\d{4}$', 'Station code must be 4 digits.')],
        editable=False,  # Makes it read-only in admin/forms
        blank=True       # Allows it to be blank before save() populates it
    )
    location_details = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.station_code})"

    def save(self, *args, **kwargs):
        if not self.station_code:  # If station_code is not provided
            self.station_code = generate_unique_code(PetrolStation, 'station_code', length=4)
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Petrol Station"
        verbose_name_plural = "Petrol Stations"
        ordering = ["name"]


class FuelTicket(DefaultModel):
    class FuelType(models.TextChoices):
        PETROL = "PETROL", "Petrol"
        DIESEL = "DIESEL", "Diesel"

    ticket_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    dispatched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="fuel_tickets_dispatched"
    )
    fuel_type = models.CharField(max_length=10, choices=FuelType.choices)
    quantity_liters = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    bill_amount = models.DecimalField(max_digits=10,
                                    decimal_places=2,
                                    default=Decimal("0.00"))

    # For vehicles not in the system or quick entry
    vehicle_registration_number = models.CharField(max_length=20, blank=True, null=True)
    # Link to an existing vehicle model if available and applicable
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="fuel_tickets"
    )
    
    remarks = models.TextField(blank=True, null=True)
    
    is_consumed = models.BooleanField(default=False, db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True)

    consumed_by_station = models.ForeignKey(
        PetrolStation,
        on_delete=models.SET_NULL, # Or models.PROTECT if station deletion should prevent ticket consumption update
        null=True, blank=True,
        related_name="consumed_fuel_tickets"
    )
    
    # Extra fields for non-system vehicles/drivers if needed
    driver_name = models.CharField(max_length=100, blank=True, null=True)
    driver_phone = models.CharField(max_length=20, blank=True, null=True)


    def __str__(self):
        return f"Ticket {str(self.ticket_id)[:8]} for {self.quantity_liters}L of {self.fuel_type}"

    class Meta:
        verbose_name = "Fuel Ticket"
        verbose_name_plural = "Fuel Tickets"
        ordering = ["-created_at"]

    def mark_as_consumed(self, station: PetrolStation, commit=True):
        if not self.is_consumed:
            self.is_consumed = True
            self.consumed_at = models.functions.Now() # Requires: from django.db.models import functions
            self.consumed_by_station = station
            if commit:
                # bill_amount is set on the instance before this method is called by the serializer
                self.save(update_fields=['is_consumed', 'consumed_at', 'consumed_by_station', 'bill_amount'])
        # else: raise some error or handle already consumed case