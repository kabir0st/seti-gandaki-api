from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from core.utils.viewsets import DefaultViewSet
from statements.models.payments import Payment
from statements.serializers import PaymentSerializer
from statements.apis.filtersets.payment import PaymentFilterSet
from django.db.models import Sum

class PaymentViewSet(DefaultViewSet):
    """
    API endpoint that allows payments to be viewed or edited.
    """
    queryset = Payment.objects.all().select_related('invoice', 'purchase_bill', 'expense', 'created_by').order_by('-created_at')
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = PaymentFilterSet
    search_fields = [
        'invoice__invoice_number',
        'purchase_bill__purchase_bill_number',
        'expense__bill_number', # Assuming Expense has a bill_number
        'remarks',
        'created_by__username', # Assuming UserBase has a username
    ]
    ordering_fields = ['amount', 'created_at', 'updated_at', 'header']

    @action(detail=True, methods=['get'], url_path='refund')
    def refund_payment(self, request, pk=None):
        """
        Marks a payment as refunded.
        """
        payment = self.get_object()
        if payment.is_refunded:
            return Response({'detail': 'Payment already refunded.'}, status=status.HTTP_400_BAD_REQUEST)
        payment.is_refunded = True
        payment.save()
        serializer = self.get_serializer(payment)
        return Response(serializer.data)    
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # Exclude refunded payments
        queryset = queryset.filter(is_refunded=False)
        stats = queryset.values('header', 'action').annotate(
            total_amount=Sum('amount')
        ).order_by('header', 'action')
        # Format stats into the desired structure
        formatted_stats = {}
        for stat in stats:
            header = stat['header']
            action = stat['action']
            amount = stat['total_amount'] or 0
            if header not in formatted_stats:
                formatted_stats[header] = {}
            formatted_stats[header][action] = float(amount)
        response_properties = {
            'payment_stats': formatted_stats
        }
        response = super().list(request, *args, **kwargs)
        response['response-properties'] = response_properties
        return response