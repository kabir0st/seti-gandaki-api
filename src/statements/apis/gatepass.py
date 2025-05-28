from django.utils import timezone
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.utils.viewsets import DefaultViewSet

from ..models.logistics import GatePass
# GatePassMovement is used by GatePassMovementSerializer below
from ..serializers import GatePassSerializer, GatePassMovementSerializer
from .filtersets import GatePassFilterSet


class GatePassViewSet(DefaultViewSet):
    """
    API endpoint that allows gate passes to be viewed or edited.
    Handles multiple entries and exits for a single gate pass.
    """
    queryset = GatePass.objects.all().select_related(
        'vehicle', 'issued_by').prefetch_related('movements').order_by(
            '-created_at')  # Order by issue time
    serializer_class = GatePassSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = GatePassFilterSet
    search_fields = [
        'vehicle__license_plate',
        'license_plate',
        'purpose',
        'driver_name',
        'driver_phone',
        'issued_by__username',
        'issued_by__first_name',
        'issued_by__last_name',
        'remarks',
    ]

    @action(detail=True, methods=['GET'], url_path='record-exit')
    def record_exit(self, request, pk=None):
        """
        Records an exit for the given gate pass.
        """
        gate_pass = self.get_object()
        # Check if last movement was an exit without a subsequent entry.
        last_movement = gate_pass.movements.order_by('-created_at').first()
        if (last_movement and last_movement.exit_time
                and not last_movement.entry_time):
            error_msg = (
                "Cannot record exit. Last movement was already an exit "
                "without a subsequent entry.")
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        movement_data = {
            'gate_pass': gate_pass.pk,
            'exit_time': timezone.now()
        }
        serializer = GatePassMovementSerializer(data=movement_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['GET'], url_path='record-entry')
    def record_entry(self, request, pk=None):
        """
        Records an entry for the given gate pass.
        """
        gate_pass = self.get_object()
        # Check if the last movement was an exit
        last_movement = gate_pass.movements.order_by('-created_at').first()
        if not last_movement:
            # This is for external vehicles primarily, first movement is entry
            # For company vehicles, an exit should be recorded first.
            # We can add a check here based on vehicle type if needed.
            pass  # Allow first movement to be entry
        elif last_movement.entry_time:
            return Response(
                {
                    "error":
                    "Cannot record entry. Last movement was already an entry."
                },
                status=status.HTTP_400_BAD_REQUEST)
        elif not last_movement.exit_time:
            return Response(
                {
                    "error":
                    "Cannot record entry. Last movement was not an exit."
                },
                status=status.HTTP_400_BAD_REQUEST)

        movement_data = {
            'gate_pass': gate_pass.pk,
            'entry_time': timezone.now()
        }
        # INFO: Each call to record-entry/record-exit creates a new
        # GatePassMovement. If the same movement record needs to be
        # updated for an exit then entry, this logic would need modification
        # to fetch and update `last_movement`. The current model structure
        # (separate exit_time, entry_time fields) implies separate records
        # or a more complex state machine on a single movement.

        serializer = GatePassMovementSerializer(data=movement_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
