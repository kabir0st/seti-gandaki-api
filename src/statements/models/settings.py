from django.db import models
from core.utils.models import SingletonModel

from .business import Business


class StatementSettings(SingletonModel):

    fiscal_year_change_month_in_bs = models.PositiveIntegerField(default=4)
    fiscal_year_change_day_in_bs = models.PositiveIntegerField(default=1)

    default_quick_invoice_business = models.ForeignKey(
        Business, on_delete=models.PROTECT, related_name='settings')

    sales_note = models.TextField(default='Thank you for you business.')
