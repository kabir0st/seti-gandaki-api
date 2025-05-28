from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from core.utils.viewsets import DefaultViewSet
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from statements.models.expense import ExpenseCategory, Expense, ExpenseItem
from statements.serializers import ExpenseCategorySerializer, ExpenseSerializer, ExpenseItemSerializer


class ExpenseCategoryViewSet(DefaultViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    lookup_field = 'id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']


class ExpenseViewSet(DefaultViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    lookup_field = 'id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['title', 'description']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Prefetch related expense items to reduce queries
        queryset = queryset.prefetch_related('expense_items')
        return queryset


class ExpenseItemViewSet(DefaultViewSet):
    serializer_class = ExpenseItemSerializer
    lookup_field = 'id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['description']

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'expense_pk',
                openapi.IN_PATH,
                description="ID of the Expense",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'expense_pk',
                openapi.IN_PATH,
                description="ID of the Expense",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        expense_pk = self.kwargs.get('expense_pk')
        if expense_pk:
            return ExpenseItem.objects.filter(expense_id=expense_pk)
        return ExpenseItem.objects.all()