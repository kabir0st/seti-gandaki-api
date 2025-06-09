from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from core.utils.viewsets import DefaultViewSet
from statements.models.payments import Payment
from statements.serializers import PaymentSerializer
from statements.apis.filtersets.payment import PaymentFilterSet


class PaymentViewSet(DefaultViewSet):
    """
    API endpoint that allows payments to be viewed or edited.
    """
    queryset = Payment.objects.all().order_by('-created_at')
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