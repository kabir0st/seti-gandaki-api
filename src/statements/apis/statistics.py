from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from statements.models.expense import Expense
from statements.models.purchase_invoice import PurchaseBill
from statements.models.invoice import Invoice

class StatementStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        period = request.query_params.get('period', 'month')  # day, week, month, year

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = timezone.now() - timedelta(days=30)  # Default last 30 days

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date = timezone.now()

        # Get statistics for each type
        invoice_stats = self._get_invoice_statistics(start_date, end_date)
        expense_stats = self._get_expense_statistics(start_date, end_date)
        purchase_stats = self._get_purchase_statistics(start_date, end_date)

        return Response({
            'invoices': invoice_stats,
            'expenses': expense_stats,
            'purchases': purchase_stats,
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }
        })

    def _get_invoice_statistics(self, start_date, end_date):
        invoices = Invoice.objects.filter(
            created_at__range=(start_date, end_date)
        )
        
        return {
            'total_count': invoices.count(),
            'total_amount': invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'average_amount': invoices.aggregate(Avg('total_amount'))['total_amount__avg'] or 0,
            'paid_count': invoices.filter(status='PAID').count(),
            'pending_count': invoices.filter(status='PENDING').count(),
            'overdue_count': invoices.filter(status='OVERDUE').count(),
            'payment_stats': {
                'cash': invoices.filter(payment_method='CASH').count(),
                'bank': invoices.filter(payment_method='BANK').count(),
                'other': invoices.filter(payment_method='OTHER').count(),
            }
        }

    def _get_expense_statistics(self, start_date, end_date):
        expenses = Expense.objects.filter(
            created_at__range=(start_date, end_date)
        )
        
        return {
            'total_count': expenses.count(),
            'total_amount': expenses.aggregate(Sum('amount'))['amount__sum'] or 0,
            'average_amount': expenses.aggregate(Avg('amount'))['amount__avg'] or 0,
            'by_category': expenses.values('category').annotate(
                count=Count('id'),
                total=Sum('amount')
            ),
            'payment_stats': {
                'cash': expenses.filter(payment_method='CASH').count(),
                'bank': expenses.filter(payment_method='BANK').count(),
                'other': expenses.filter(payment_method='OTHER').count(),
            }
        }

    def _get_purchase_statistics(self, start_date, end_date):
        purchases = PurchaseBill.objects.filter(
            created_at__range=(start_date, end_date)
        )
        
        return {
            'total_count': purchases.count(),
            'total_amount': purchases.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'average_amount': purchases.aggregate(Avg('total_amount'))['total_amount__avg'] or 0,
            'paid_count': purchases.filter(status='PAID').count(),
            'pending_count': purchases.filter(status='PENDING').count(),
            'by_supplier': purchases.values('supplier__name').annotate(
                count=Count('id'),
                total=Sum('total_amount')
            ),
            'payment_stats': {
                'cash': purchases.filter(payment_method='CASH').count(),
                'bank': purchases.filter(payment_method='BANK').count(),
                'other': purchases.filter(payment_method='OTHER').count(),
            }
        } 