from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from statements.apis.filtersets.cashcounter import CashCounterFilterSet
from rest_framework import viewsets
from statements.models import CashCounter
from statements.serializers import CashCounterSerializer

class CashCounterViewSet(viewsets.ModelViewSet):
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