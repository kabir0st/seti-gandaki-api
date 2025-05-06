from django.db import models


class SingletonModel(models.Model):
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        # TODO Make it raise NotImplementedError
        # Because every model should implement their
        # own `load` method.
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
