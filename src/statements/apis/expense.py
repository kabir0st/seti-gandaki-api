from rest_framework import viewsets
from statements.models.expense import ExpenseCategory, Expense, ExpenseItem
from statements.serializers import ExpenseCategorySerializer, ExpenseSerializer, ExpenseItemSerializer


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    lookup_field = 'id'


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    lookup_field = 'id'

    def get_queryset(self):
        queryset = super().get_queryset()
        # Prefetch related expense items to reduce queries
        queryset = queryset.prefetch_related('expense_items')
        return queryset


class ExpenseItemViewSet(viewsets.ModelViewSet):
    queryset = ExpenseItem.objects.all()
    serializer_class = ExpenseItemSerializer
    lookup_field = 'id'