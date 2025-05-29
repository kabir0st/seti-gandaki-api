from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from statements.models.support import Staff


class SalaryDisbursement(models.Model):
    staff = models.ForeignKey(Staff,
                              on_delete=models.PROTECT,
                              related_name='salary_disbursements',
                              verbose_name=_("Staff"))
    from_date = models.DateField(_("From Date"))
    to_date = models.DateField(_("To Date"))
    amount = models.DecimalField(_("Amount"),
                                 max_digits=10,
                                 decimal_places=2)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_salary_disbursements',
        verbose_name=_("Created By"),
        null=True,
        blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Salary Disbursement")
        verbose_name_plural = _("Salary Disbursements")
        ordering = ["-created_at", "staff"]

    def __str__(self):
        return f"Salary for {self.staff} from {self.from_date} to {self.to_date}"