from rest_framework.exceptions import ValidationError
from core.utils.viewsets import DefaultViewSet
from statements.models.expense import ExpenseCategory, Expense, ExpenseItem
from statements.serializers import ExpenseCategorySerializer, ExpenseSerializer, ExpenseItemSerializer


class ExpenseCategoryViewSet(DefaultViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    lookup_field = 'id'
    search_fields = ['name']


class ExpenseViewSet(DefaultViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    lookup_field = 'id'
    search_fields = ['title', 'description']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Prefetch related expense items to reduce queries
        queryset = queryset.prefetch_related('expense_items')
        return queryset


class ExpenseItemViewSet(DefaultViewSet):
    serializer_class = ExpenseItemSerializer
    lookup_field = 'id'
    search_fields = ['item_name']


    def get_queryset(self):
        expense_id = self.kwargs.get('expense_id')
        if expense_id:
            return ExpenseItem.objects.filter(expense_id=expense_id)
        return ExpenseItem.objects.none()