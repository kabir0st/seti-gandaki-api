from rest_framework import  status, permissions,  views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import models
from core.utils.viewsets import DefaultViewSet

from hrm.models.fuel import FuelTicket, PetrolStation
from hrm.serializers import ( 
    PetrolStationSerializer, 
    FuelTicketSerializer,
    FuelTicketConsumeSerializer,
    FuelTicketPublicDetailSerializer
)

class PetrolStationViewSet(DefaultViewSet):
    queryset = PetrolStation.objects.filter()
    serializer_class = PetrolStationSerializer
    # permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        method='get',
        manual_parameters=[
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start date for filtering consumed tickets (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End date for filtering consumed tickets (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('fuel_type', openapi.IN_QUERY, description="Filter by fuel type (PETROL or DIESEL)", type=openapi.TYPE_STRING, enum=[choice[0] for choice in FuelTicket.FuelType.choices]),
        ],
        responses={
            200: openapi.Response(
                description="Statistics for the petrol station",
                examples={
                    "application/json": {
                        "station_name": "Main Street Station",
                        "station_code": "1001",
                        "filters_applied": {
                            "start_date": "2023-01-01",
                            "end_date": "2023-01-31",
                            "fuel_type": "DIESEL"
                        },
                        "total_tickets_verified": 50,
                        "fuel_dispersed": {
                            "petrol_liters": 0.00,
                            "diesel_liters": 1250.75,
                            "total_liters": 1250.75
                        },
                        "period_coverage": {
                             "earliest_ticket_date": "2023-01-05T10:00:00Z",
                             "latest_ticket_date": "2023-01-28T15:30:00Z"
                        }
                    }
                }
            )
        }
    )
    @action(detail=True, methods=['get'], url_path='stats')
    def stats(self, request, pk=None):
        station = self.get_object()
        
        tickets_queryset = FuelTicket.objects.filter(
            consumed_by_station=station,
            is_consumed=True
        )

        # Apply filters
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        fuel_type_filter = request.query_params.get('fuel_type')

        applied_filters = {}

        if start_date_str:
            try:
                start_date = timezone.datetime.strptime(start_date_str, "%Y-%m-%d").date()
                tickets_queryset = tickets_queryset.filter(consumed_at__date__gte=start_date)
                applied_filters['start_date'] = start_date_str
            except ValueError:
                return Response({"error": "Invalid start_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        if end_date_str:
            try:
                end_date = timezone.datetime.strptime(end_date_str, "%Y-%m-%d").date()
                tickets_queryset = tickets_queryset.filter(consumed_at__date__lte=end_date)
                applied_filters['end_date'] = end_date_str
            except ValueError:
                return Response({"error": "Invalid end_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        if fuel_type_filter:
            if fuel_type_filter.upper() in FuelTicket.FuelType.values:
                tickets_queryset = tickets_queryset.filter(fuel_type=fuel_type_filter.upper())
                applied_filters['fuel_type'] = fuel_type_filter.upper()
            else:
                return Response({"error": f"Invalid fuel_type. Choose from {FuelTicket.FuelType.labels}."}, status=status.HTTP_400_BAD_REQUEST)

        total_tickets_verified = tickets_queryset.count()

        fuel_aggregation = tickets_queryset.aggregate(
            total_petrol=Sum('quantity_liters', filter=Q(fuel_type=FuelTicket.FuelType.PETROL)),
            total_diesel=Sum('quantity_liters', filter=Q(fuel_type=FuelTicket.FuelType.DIESEL))
        )

        petrol_liters = fuel_aggregation.get('total_petrol') or 0
        diesel_liters = fuel_aggregation.get('total_diesel') or 0
        total_liters = petrol_liters + diesel_liters
        
        period_data = tickets_queryset.aggregate(
            earliest_date=models.Min('consumed_at'),
            latest_date=models.Max('consumed_at')
        )

        response_data = {
            "station_name": station.name,
            "station_code": station.station_code,
            "filters_applied": applied_filters,
            "total_tickets_verified": total_tickets_verified,
            "fuel_dispersed": {
                "petrol_liters": round(float(petrol_liters), 2),
                "diesel_liters": round(float(diesel_liters), 2),
                "total_liters": round(float(total_liters), 2)
            },
            "period_coverage": {
                "earliest_ticket_date": period_data.get('earliest_date').isoformat() if period_data.get('earliest_date') else None,
                "latest_ticket_date": period_data.get('latest_date').isoformat() if period_data.get('latest_date') else None,
            }
        }
        return Response(response_data)

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

class FuelingStatsAPIView(views.APIView):
    permission_classes = [permissions.IsAdminUser] # Or a more specific permission

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start date for filtering tickets (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End date for filtering tickets (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('fuel_type', openapi.IN_QUERY, description="Filter by fuel type (PETROL or DIESEL)", type=openapi.TYPE_STRING, enum=[choice[0] for choice in FuelTicket.FuelType.choices]),
            openapi.Parameter('station_id', openapi.IN_QUERY, description="Filter by specific petrol station ID", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(
                description="Overall fueling statistics",
                examples={
                    "application/json": {
                        "filters_applied": {
                            "start_date": "2023-01-01",
                            "end_date": "2023-12-31",
                            "fuel_type": "PETROL",
                            "station_id": 1
                        },
                        "total_tickets_created": 1200,
                        "total_fuel_dispatched": {
                            "petrol_liters": 15000.50,
                            "diesel_liters": 25000.00,
                            "total_liters": 40000.50
                        },
                        "total_tickets_consumed": 1150,
                        "total_fuel_consumed": {
                            "petrol_liters": 14500.25,
                            "diesel_liters": 24000.75,
                            "total_liters": 38501.00
                        },
                         "period_coverage_created": {
                             "earliest_ticket_date": "2023-01-02T08:00:00Z",
                             "latest_ticket_date": "2023-12-30T18:00:00Z"
                        },
                        "period_coverage_consumed": {
                             "earliest_ticket_date": "2023-01-02T09:00:00Z",
                             "latest_ticket_date": "2023-12-30T19:00:00Z"
                        }
                    }
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        all_tickets_queryset = FuelTicket.objects.all()
        consumed_tickets_queryset = FuelTicket.objects.filter(is_consumed=True)

        # Apply filters
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        fuel_type_filter = request.query_params.get('fuel_type')
        station_id_filter = request.query_params.get('station_id')

        applied_filters = {}

        if start_date_str:
            try:
                start_date = timezone.datetime.strptime(start_date_str, "%Y-%m-%d").date()
                all_tickets_queryset = all_tickets_queryset.filter(created_at__date__gte=start_date)
                consumed_tickets_queryset = consumed_tickets_queryset.filter(consumed_at__date__gte=start_date)
                applied_filters['start_date'] = start_date_str
            except ValueError:
                return Response({"error": "Invalid start_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        if end_date_str:
            try:
                end_date = timezone.datetime.strptime(end_date_str, "%Y-%m-%d").date()
                all_tickets_queryset = all_tickets_queryset.filter(created_at__date__lte=end_date)
                consumed_tickets_queryset = consumed_tickets_queryset.filter(consumed_at__date__lte=end_date)
                applied_filters['end_date'] = end_date_str
            except ValueError:
                return Response({"error": "Invalid end_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        if fuel_type_filter:
            if fuel_type_filter.upper() in FuelTicket.FuelType.values:
                fuel_type_val = fuel_type_filter.upper()
                all_tickets_queryset = all_tickets_queryset.filter(fuel_type=fuel_type_val)
                consumed_tickets_queryset = consumed_tickets_queryset.filter(fuel_type=fuel_type_val)
                applied_filters['fuel_type'] = fuel_type_val
            else:
                return Response({"error": f"Invalid fuel_type. Choose from {FuelTicket.FuelType.labels}."}, status=status.HTTP_400_BAD_REQUEST)
        
        if station_id_filter:
            try:
                station_id = int(station_id_filter)
                # For "all_tickets_queryset", if a station_id is provided, we interpret this as
                # tickets that were *eventually consumed* by this station.
                # This aligns "dispatched" with a station context when specified.
                all_tickets_queryset = all_tickets_queryset.filter(consumed_by_station_id=station_id)
                consumed_tickets_queryset = consumed_tickets_queryset.filter(consumed_by_station_id=station_id)
                applied_filters['station_id'] = station_id
                
                # Check if the station exists to provide a better error message
                if not PetrolStation.objects.filter(id=station_id).exists():
                    return Response({"error": f"PetrolStation with id {station_id} not found."}, status=status.HTTP_404_NOT_FOUND)
                    
            except ValueError:
                return Response({"error": "Invalid station_id. Must be an integer."}, status=status.HTTP_400_BAD_REQUEST)


        # Stats for all created/dispatched tickets
        total_tickets_created = all_tickets_queryset.count()
        dispatched_aggregation = all_tickets_queryset.aggregate(
            total_petrol=Sum('quantity_liters', filter=Q(fuel_type=FuelTicket.FuelType.PETROL)),
            total_diesel=Sum('quantity_liters', filter=Q(fuel_type=FuelTicket.FuelType.DIESEL))
        )
        dispatched_petrol = dispatched_aggregation.get('total_petrol') or 0
        dispatched_diesel = dispatched_aggregation.get('total_diesel') or 0
        
        period_created_data = all_tickets_queryset.aggregate(
            earliest_date=models.Min('created_at'),
            latest_date=models.Max('created_at')
        )

        # Stats for consumed tickets
        total_tickets_consumed = consumed_tickets_queryset.count()
        consumed_aggregation = consumed_tickets_queryset.aggregate(
            total_petrol=Sum('quantity_liters', filter=Q(fuel_type=FuelTicket.FuelType.PETROL)),
            total_diesel=Sum('quantity_liters', filter=Q(fuel_type=FuelTicket.FuelType.DIESEL))
        )
        consumed_petrol = consumed_aggregation.get('total_petrol') or 0
        consumed_diesel = consumed_aggregation.get('total_diesel') or 0

        period_consumed_data = consumed_tickets_queryset.aggregate(
            earliest_date=models.Min('consumed_at'),
            latest_date=models.Max('consumed_at')
        )

        response_data = {
            "filters_applied": applied_filters,
            "total_tickets_created": total_tickets_created,
            "total_fuel_dispatched": {
                "petrol_liters": round(float(dispatched_petrol), 2),
                "diesel_liters": round(float(dispatched_diesel), 2),
                "total_liters": round(float(dispatched_petrol + dispatched_diesel), 2)
            },
            "total_tickets_consumed": total_tickets_consumed,
            "total_fuel_consumed": {
                "petrol_liters": round(float(consumed_petrol), 2),
                "diesel_liters": round(float(consumed_diesel), 2),
                "total_liters": round(float(consumed_petrol + consumed_diesel), 2)
            },
            "period_coverage_created": {
                "earliest_ticket_date": period_created_data.get('earliest_date').isoformat() if period_created_data.get('earliest_date') else None,
                "latest_ticket_date": period_created_data.get('latest_date').isoformat() if period_created_data.get('latest_date') else None,
            },
            "period_coverage_consumed": {
                "earliest_ticket_date": period_consumed_data.get('earliest_date').isoformat() if period_consumed_data.get('earliest_date') else None,
                "latest_ticket_date": period_consumed_data.get('latest_date').isoformat() if period_consumed_data.get('latest_date') else None,
            }
        }
        return Response(response_data)