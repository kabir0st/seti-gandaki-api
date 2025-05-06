from core.utils.models import DefaultModel
from django.db import models

from .user import UserBase


class AuthenticationLog(DefaultModel):
    LOGIN_STATUS = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_refresh', 'Login Refresh'),
    )
    user = models.ForeignKey(UserBase, on_delete=models.CASCADE)
    ip = models.GenericIPAddressField(null=True, blank=True)
    datetime = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=15,
                              choices=LOGIN_STATUS,
                              null=True,
                              blank=True)

    def __str__(self):
        return f'{self.user} {self.action}'
