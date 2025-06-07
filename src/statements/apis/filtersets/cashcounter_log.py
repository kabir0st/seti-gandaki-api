import django_filters

from statements.models.cashcounter_log import CashCounterLog

class CashCounterLogFilterSet(django_filters.FilterSet):
    class Meta:
        model = CashCounterLog
        fields = "__all__"