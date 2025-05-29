from django.utils import timezone
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from hrm.models import FoodTicket
from hrm.serializers import FoodTicketSerializer, FoodTicketMarkAsUsedSerializer
from .filtersets.food_ticket import FoodTicketFilterSet
from core.utils.permissions import IsStaffOrReadOnly # Removed IsOwnerOrStaff


class FoodTicketViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Food Tickets.

    Provides CRUD operations for food tickets.
    Includes an action to mark a ticket as used and an action to get usage statistics.

    Filtering options:
    - `staff_id`: Filter by staff member ID.
    - `issued_by_id`: Filter by the ID of the user who issued the ticket.
    - `meal_type`: Filter by meal type (e.g., 'lunch', 'dinner').
    - `is_used`: Filter by whether the ticket has been used (true/false).
    - `issued_at_after`: Filter for tickets issued after a specific datetime.
    - `issued_at_before`: Filter for tickets issued before a specific datetime.
    - `used_at_after`: Filter for tickets used after a specific datetime.
    - `used_at_before`: Filter for tickets used before a specific datetime.
    """
    queryset = FoodTicket.objects.select_related('staff', 'issued_by').all()
    serializer_class = FoodTicketSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly] # Staff can CRUD, others can only read
    filter_backends = [DjangoFilterBackend]
    filterset_class = FoodTicketFilterSet

    def get_serializer_class(self):
        if self.action == 'mark_as_used':
            return FoodTicketMarkAsUsedSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(issued_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStaffOrReadOnly]) # Staff can mark as used
    def mark_as_used(self, request, pk=None):
        """
        Marks a specific food ticket as used.
        """
        ticket = self.get_object()
        serializer = self.get_serializer(instance=ticket, data=request.data) # request.data might be empty
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Return the updated ticket data using the main serializer
        return Response(FoodTicketSerializer(ticket, context={'request': request}).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsStaffOrReadOnly]) # Staff can view stats
    def statistics(self, request):
        """
        Provides statistics about food ticket usage.

        Includes:
        - Total tickets issued.
        - Total tickets used.
        - Total tickets unused.
        - Tickets issued per meal type.
        - Tickets used per meal type.
        - Tickets issued today.
        - Tickets used today.
        """
        # Apply filters from query parameters to the base queryset for stats
        # This allows stats to be generated for a filtered subset of tickets
        # For example, /api/hrm/food-tickets/statistics/?staff_id=123
        # or /api/hrm/food-tickets/statistics/?issued_at_after=2024-01-01T00:00:00Z

        # Note: The filterset_class will handle the actual filtering if applied to the viewset.
        # If we want stats on the *filtered* queryset from the list view, we can use self.filter_queryset.
        # However, for general stats, using the base queryset or applying specific common filters might be better.
        # For now, let's use the viewset's default queryset and allow it to be filtered by filter_backends.
        
        queryset = self.filter_queryset(self.get_queryset())


        total_issued = queryset.count()
        total_used = queryset.filter(is_used=True).count()
        total_unused = total_issued - total_used

        meal_type_issued_stats = list(queryset.values('meal_type')
                                      .annotate(count=Count('id'))
                                      .order_by('-count'))

        meal_type_used_stats = list(queryset.filter(is_used=True)
                                    .values('meal_type')
                                    .annotate(count=Count('id'))
                                    .order_by('-count'))
        
        today = timezone.now().date()
        issued_today = queryset.filter(issued_at__date=today).count()
        used_today = queryset.filter(is_used=True, used_at__date=today).count()

        # You could also add stats like:
        # - Most active staff (issuing tickets)
        # - Staff with most tickets received
        # - Average time to use a ticket

        return Response({
            'total_tickets_issued': total_issued,
            'total_tickets_used': total_used,
            'total_tickets_unused': total_unused,
            'tickets_issued_per_meal_type': meal_type_issued_stats,
            'tickets_used_per_meal_type': meal_type_used_stats,
            'tickets_issued_today': issued_today,
            'tickets_used_today': used_today,
        }, status=status.HTTP_200_OK)

    # Example of more specific permission for object-level control if needed
    # def get_permissions(self):
    #     if self.action in ['update', 'partial_update', 'destroy']:
    #         # Only owner (issued_by) or staff can modify/delete
    #         # Or perhaps only staff if tickets are centrally managed
    #         return [IsAuthenticated(), IsOwnerOrStaff()] # IsOwnerOrStaff checks obj.issued_by
    #     return super().get_permissions()