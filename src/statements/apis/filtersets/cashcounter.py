import django_filters
from statements.models import CashCounter

class CashCounterFilterSet(django_filters.FilterSet):
    class Meta:
        model = CashCounter
        fields = {
            'counter_name': ['exact', 'icontains'],
        }