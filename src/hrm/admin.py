from django.contrib import admin
from .models.fuel import PetrolStation, FuelTicket
from .models.attendance import Attendance # Import Attendance model
from unfold.admin import ModelAdmin

@admin.register(PetrolStation)
class PetrolStationAdmin(ModelAdmin):
    list_display = ('name', 'station_code', 'location_details', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'station_code')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(FuelTicket)
class FuelTicketAdmin(ModelAdmin):
    list_display = (
        'ticket_id', 'dispatched_by', 'fuel_type', 'quantity_liters', 
        'vehicle_registration_number', 'is_consumed', 'consumed_at', 
        'consumed_by_station', 'created_at'
    )
    search_fields = (
        'ticket_id__iexact', 'dispatched_by__username', 'vehicle_registration_number', 
        'consumed_by_station__name', 'consumed_by_station__station_code'
    )
    list_filter = ('fuel_type', 'is_consumed', 'created_at', 'consumed_at', 'dispatched_by', 'consumed_by_station')
    readonly_fields = ('created_at', 'updated_at', 'consumed_at', 'ticket_id')
    autocomplete_fields = ['dispatched_by', 'consumed_by_station']
    
    fieldsets = (
        (None, {
            'fields': ('ticket_id', 'dispatched_by', 'fuel_type', 'quantity_liters')
        }),
        ('Vehicle Information (Optional)', {
            'fields': ('vehicle_registration_number', 'driver_name', 'driver_phone'),
            # 'classes': ('collapse',), # If you want it collapsed by default
        }),
        ('Consumption Details', {
            'fields': ('is_consumed', 'consumed_at', 'consumed_by_station')
        }),
        ('Additional Information', {
            'fields': ('remarks',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_consumed: # if ticket is consumed, make most fields readonly
            readonly.extend([
                'dispatched_by', 'fuel_type', 'quantity_liters', 
                'vehicle_registration_number', 'driver_name', 'driver_phone', 'remarks',
                'consumed_by_station' # Allow changing station if error? Or lock it?
            ])
        return readonly

@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    list_display = ('staff', 'date', 'check_in_time', 'check_out_time', 'status', 'created_at', 'updated_at')
    search_fields = ('staff__name', 'staff__pan', 'date')
    list_filter = ('status', 'date', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['staff']
    date_hierarchy = 'date'

    fieldsets = (
        (None, {
            'fields': ('staff', 'date', 'status')
        }),
        ('Timings', {
            'fields': ('check_in_time', 'check_out_time')
        }),
        ('Additional Information', {
            'fields': ('remarks',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
