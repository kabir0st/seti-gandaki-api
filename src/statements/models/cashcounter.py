from django.db import models

class CashCounter(models.Model):
    """
    Model to store the count of Nepali currency denominations for petty cash.
    """
    counter_name = models.CharField(max_length=100, default="cash counter", help_text="Name of the cash counter")
    denomination_1000 = models.PositiveIntegerField(default=0, help_text="Count of 1000 Rupee notes")
    denomination_500 = models.PositiveIntegerField(default=0, help_text="Count of 500 Rupee notes")
    denomination_100 = models.PositiveIntegerField(default=0, help_text="Count of 100 Rupee notes")
    denomination_50 = models.PositiveIntegerField(default=0, help_text="Count of 50 Rupee notes")
    denomination_20 = models.PositiveIntegerField(default=0, help_text="Count of 20 Rupee notes")
    denomination_10 = models.PositiveIntegerField(default=0, help_text="Count of 10 Rupee notes")
    denomination_5 = models.PositiveIntegerField(default=0, help_text="Count of 5 Rupee notes")
    denomination_2 = models.PositiveIntegerField(default=0, help_text="Count of 2 Rupee notes")
    denomination_1 = models.PositiveIntegerField(default=0, help_text="Count of 1 Rupee notes")

    def __str__(self):
        return self.counter_name

    def total_amount(self):
        """Calculates the total amount of cash."""
        return (
            self.denomination_1000 * 1000 +
            self.denomination_500 * 500 +
            self.denomination_100 * 100 +
            self.denomination_50 * 50 +
            self.denomination_20 * 20 +
            self.denomination_10 * 10 +
            self.denomination_5 * 5 +
            self.denomination_2 * 2 +
            self.denomination_1 * 1
        )

    class Meta:
        verbose_name = "Cash Counter"
        verbose_name_plural = "Cash Counters"