import uuid

from django.db import models

from core.utils.models import DefaultModel


class Document(DefaultModel):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=255, blank=True, null=True)
    model = models.CharField(max_length=255)
    status = models.CharField(max_length=255, default='processing')
    document = models.FileField(null=True, blank=True)

    def __str__(self):
        return f'{self.model}: {self.uuid}'


class FAQ(models.Model):
    question = models.TextField(default='')
    answer = models.TextField(default='')
    priority = models.IntegerField(default=5)

    def __str__(self):
        return self.question


class Inquiries(DefaultModel):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
