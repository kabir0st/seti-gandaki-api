from django.contrib import admin
from .models.fuel import PetrolStation, FuelTicket
from .models.attendance import Attendance  # Import Attendance model
from .models.salary import SalaryDisbursement  # Import SalaryDisbursement model
from .models.food_ticket import FoodTicket  # Import FoodTicket model
from unfold.admin import ModelAdmin


@admin.register(PetrolStation)
class PetrolStationAdmin(ModelAdmin):
    list_display = ('name', 'station_code', 'location_details', 'is_active',
                    'created_at', 'updated_at')
    search_fields = ('name', 'station_code')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FuelTicket)
class FuelTicketAdmin(ModelAdmin):
    list_display = ('ticket_id', 'dispatched_by', 'fuel_type',
                    'quantity_liters', 'vehicle_registration_number',
                    'is_consumed', 'consumed_at', 'consumed_by_station',
                    'created_at')
    search_fields = ('ticket_id__iexact', 'dispatched_by__username',
                     'vehicle_registration_number',
                     'consumed_by_station__name',
                     'consumed_by_station__station_code')
    list_filter = ('fuel_type', 'is_consumed', 'created_at', 'consumed_at',
                   'dispatched_by', 'consumed_by_station')
    readonly_fields = ('created_at', 'updated_at', 'consumed_at', 'ticket_id')
    autocomplete_fields = ['dispatched_by', 'consumed_by_station']

    fieldsets = (
        (None, {
            'fields':
            ('ticket_id', 'dispatched_by', 'fuel_type', 'quantity_liters')
        }),
        (
            'Vehicle Information (Optional)',
            {
                'fields':
                ('vehicle_registration_number', 'driver_name', 'driver_phone'),
                # 'classes': ('collapse',), # If you want it collapsed by default
            }),
        ('Consumption Details', {
            'fields': ('is_consumed', 'consumed_at', 'consumed_by_station',
                       'bill_amount')
        }),
        ('Additional Information', {
            'fields': ('remarks', )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse', )
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_consumed:  # if ticket is consumed, make most fields readonly
            readonly.extend([
                'dispatched_by',
                'fuel_type',
                'quantity_liters',
                'vehicle_registration_number',
                'driver_name',
                'driver_phone',
                'remarks',
                'consumed_by_station'  # Allow changing station if error? Or lock it?
            ])
        return readonly


@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    list_display = ('staff', 'date', 'time', 'attendance_type',
                    'verification_method', 'created_at')
    search_fields = ('staff__name', 'staff__pan', 'date')
    list_filter = ('attendance_type', 'verification_method', 'date',
                   'created_at')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['staff']
    date_hierarchy = 'date'

    fieldsets = (
        (None, {
            'fields': ('staff', 'date', 'time', 'attendance_type')
        }),
        ('Verification', {
            'fields': ('verification_method', )
        }),
        ('Additional Information', {
            'fields': ('remarks', )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse', )
        }),
    )


@admin.register(SalaryDisbursement)
class SalaryDisbursementAdmin(ModelAdmin):
    list_display = ('staff', 'from_date', 'to_date', 'amount', 'created_by',
                    'created_at')
    search_fields = ('staff__name', 'staff__pan', 'from_date', 'to_date')
    list_filter = ('from_date', 'to_date', 'created_at', 'created_by', 'staff')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    autocomplete_fields = ['staff', 'created_by']
    date_hierarchy = 'from_date'

    fieldsets = (
        (None, {
            'fields': ('staff', ('from_date', 'to_date'), 'amount')
        }),
        ('Additional Information', {
            'fields': ('remarks', )
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse', )
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # if creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FoodTicket)
class FoodTicketAdmin(ModelAdmin):
    list_display = ('ticket_number', 'staff', 'meal_type', 'issued_by',
                    'issued_at', 'created_at')
    search_fields = ('ticket_number__iexact', 'staff__name',
                     'staff__user__username', 'issued_by__username',
                     'meal_type')
    list_filter = ('meal_type', 'issued_at', 'staff', 'issued_by')
    readonly_fields = ('created_at', 'updated_at', 'issued_at',
                       'ticket_number', 'issued_by')
    autocomplete_fields = ['staff', 'issued_by']
    date_hierarchy = 'issued_at'

    fieldsets = (
        (None, {
            'fields': ('ticket_number', 'staff', 'meal_type', 'issued_by')
        }),
        ('Additional Information', {
            'fields': ('notes', )
        }),
        ('Timestamps', {
            'fields': ('issued_at', 'created_at', 'updated_at'),
            'classes': ('collapse', )
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and obj.pk:  # For existing objects
            readonly.append('staff')  # Make staff readonly after creation
            readonly.append(
                'meal_type')  # Make meal_type readonly after creation
        return readonly

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # If creating a new object
            obj.issued_by = request.user
        super().save_model(request, obj, form, change)
