from rest_framework import  status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from core.utils.viewsets import DefaultViewSet

from hrm.models.fuel import FuelTicket, PetrolStation
from hrm.serializers import ( 
    PetrolStationSerializer, 
    FuelTicketSerializer,
    FuelTicketConsumeSerializer,
    FuelTicketPublicDetailSerializer
)

class PetrolStationViewSet(DefaultViewSet):
    queryset = PetrolStation.objects.filter(is_active=True)
    serializer_class = PetrolStationSerializer
    # permission_classes = [permissions.IsAdminUser] 

class FuelTicketViewSet(DefaultViewSet):
    queryset = FuelTicket.objects.all() 
    serializer_class = FuelTicketSerializer
    permission_classes = [permissions.IsAuthenticated] 

    def get_queryset(self):
        user = self.request.user
        if user.is_staff: 
            return FuelTicket.objects.all().select_related('dispatched_by', 'consumed_by_station')
        return FuelTicket.objects.filter(dispatched_by=user).select_related('dispatched_by', 'consumed_by_station')

    def perform_create(self, serializer):
        serializer.save()


    @action(detail=True, methods=['post'], serializer_class=FuelTicketConsumeSerializer,
            permission_classes=[permissions.AllowAny]) 
    def consume(self, request, pk=None):
        ticket = get_object_or_404(FuelTicket, ticket_id=pk) 
        
        if ticket.is_consumed:
            return Response(
                {"error": f"Ticket already consumed at {ticket.consumed_by_station.name} on {ticket.consumed_at.strftime('%Y-%m-%d %H:%M')}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data, context={'ticket': ticket})
        if serializer.is_valid():
            serializer.save() 
            return Response(FuelTicketSerializer(ticket, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], serializer_class=FuelTicketPublicDetailSerializer,
            permission_classes=[permissions.AllowAny], url_path='verify') 
    def verify_ticket(self, request, pk=None):
        ticket = get_object_or_404(FuelTicket, ticket_id=pk)
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)