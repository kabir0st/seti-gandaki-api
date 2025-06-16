import django_filters
from hrm.models import FoodTicket
from django.contrib.auth import get_user_model

User = get_user_model()

class FoodTicketFilterSet(django_filters.FilterSet):
    """
    FilterSet for FoodTicket API.
    """
    staff_id = django_filters.CharFilter(field_name='staff__id', label='Staff ID')
    issued_by_id = django_filters.ModelChoiceFilter(
        field_name='issued_by',
        queryset=User.objects.all(), # Or filter further, e.g., User.objects.filter(is_staff=True)
        label='Issued By User ID'
    )
    meal_type = django_filters.ChoiceFilter(choices=FoodTicket.MEAL_TYPE_CHOICES, label='Meal Type')
    is_used = django_filters.BooleanFilter(field_name='is_used', label='Is Used')
    
    issued_at_after = django_filters.DateTimeFilter(field_name='issued_at', lookup_expr='gte', label='Issued At After (YYYY-MM-DDTHH:MM:SS)')
    issued_at_before = django_filters.DateTimeFilter(field_name='issued_at', lookup_expr='lte', label='Issued At Before (YYYY-MM-DDTHH:MM:SS)')
    
    used_at_after = django_filters.DateTimeFilter(field_name='used_at', lookup_expr='gte', label='Used At After (YYYY-MM-DDTHH:MM:SS)')
    used_at_before = django_filters.DateTimeFilter(field_name='used_at', lookup_expr='lte', label='Used At Before (YYYY-MM-DDTHH:MM:SS)')

    ticket_number = django_filters.CharFilter(field_name='ticket_number', lookup_expr='icontains', label='Ticket Number (contains)')

    class Meta:
        model = FoodTicket
        fields = [
            'staff_id', 
            'issued_by_id', 
            'meal_type', 
            'is_used',
            'issued_at_after',
            'issued_at_before',
            'used_at_after',
            'used_at_before',
            'ticket_number',
        ]