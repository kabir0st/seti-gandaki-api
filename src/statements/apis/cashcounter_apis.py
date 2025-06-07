from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from core.utils.viewsets import DefaultViewSet
from statements.apis.filtersets.cashcounter import CashCounterFilterSet
from statements.apis.filtersets.cashcounter_log import CashCounterLogFilterSet
from statements.models import CashCounter
from statements.models.cashcounter_log import CashCounterLog
from statements.serializers import CashCounterLogSerializer, CashCounterSerializer

class CashCounterViewSet(DefaultViewSet):
    """
    API endpoint that allows CashCounter to be viewed or edited.
    """
    queryset = CashCounter.objects.all()
    serializer_class = CashCounterSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CashCounterFilterSet

    @action(detail=True, methods=['post'])
    def calculate_change(self, request, pk=None):
        """
        Calculates the change to be returned based on given amount and bill amount,
        using available denominations in the cash counter.
        """
        cash_counter = self.get_object()
        given_amount = request.data.get('given_amount')
        bill_amount = request.data.get('bill_amount')

        if given_amount is None or bill_amount is None:
            return Response({"error": "Please provide both given_amount and bill_amount."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            given_amount = int(given_amount)
            bill_amount = int(bill_amount)
        except ValueError:
            return Response({"error": "given_amount and bill_amount must be integers."},
                            status=status.HTTP_400_BAD_REQUEST)

        change_amount = given_amount - bill_amount

        if change_amount < 0:
            return Response({"error": "Given amount is less than the bill amount."},
                            status=status.HTTP_400_BAD_REQUEST)

        if change_amount == 0:
            return Response({"change": {}, "message": "No change required."},
                            status=status.HTTP_200_OK)

        denominations = {
            1000: cash_counter.denomination_1000,
            500: cash_counter.denomination_500,
            100: cash_counter.denomination_100,
            50: cash_counter.denomination_50,
            20: cash_counter.denomination_20,
            10: cash_counter.denomination_10,
            5: cash_counter.denomination_5,
            2: cash_counter.denomination_2,
            1: cash_counter.denomination_1,
        }

        change_to_return = {}
        remaining_change = change_amount

        # Sort denominations in descending order
        sorted_denominations = sorted(denominations.keys(), reverse=True)

        for denom in sorted_denominations:
            if remaining_change >= denom:
                # Calculate how many notes/coins of this denomination are needed
                num_needed = remaining_change // denom
                # Calculate how many can actually be given based on availability
                num_to_give = min(num_needed, denominations[denom])

                if num_to_give > 0:
                    change_to_return[denom] = num_to_give
                    remaining_change -= num_to_give * denom

        if remaining_change > 0:
            return Response({
                "error": "Insufficient denominations to provide exact change.",
                "remaining_change": remaining_change,
                "change_provided": change_to_return
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({"change": change_to_return, "message": "Change calculated successfully."},
                        status=status.HTTP_200_OK)
    def create(self, request, *args, **kwargs):
        # Only allow setting the counter_name during creation
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract only the counter_name from validated data
        counter_name = serializer.validated_data.get('counter_name')

        # Create the CashCounter instance with only the counter_name
        instance = CashCounter.objects.create(counter_name=counter_name)

        # Serialize the created instance for the response
        response_serializer = self.get_serializer(instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # Only allow updating the counter_name
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Create a serializer with only the counter_name field
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Update only the counter_name if present in validated data
        if 'counter_name' in serializer.validated_data:
            instance.counter_name = serializer.validated_data['counter_name']
            instance.save(update_fields=['counter_name'])

        # Serialize the updated instance for the response
        response_serializer = self.get_serializer(instance)
        return Response(response_serializer.data)

    @action(detail=True, methods=['post'], serializer_class=CashCounterLogSerializer)
    def apply_change(self, request, pk=None):
        """
        Creates a CashCounterLog to record and apply changes to the cash counter.
        """
        cash_counter = self.get_object() # Get the specific CashCounter instance

        # Use the CashCounterLogSerializer to validate incoming data
        serializer = CashCounterLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create the CashCounterLog instance, linking it to the cash counter
        # The signals on CashCounterLog will handle the actual update to CashCounter
        serializer.save(cash_counter=cash_counter)

        return Response(
            {"message": "Cash counter change logged and applied successfully."},
            status=status.HTTP_201_CREATED
        )

class CashCounterLogViewSet(DefaultViewSet):
    """
    API endpoint that allows CashCounterLog to be viewed.
    """
    queryset = CashCounterLog.objects.all()
    serializer_class = CashCounterLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CashCounterLogFilterSet
    http_method_names = ['get', 'head', 'options'] # Only allow listing