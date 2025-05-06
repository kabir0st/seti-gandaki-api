from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from core.utils.functions import invalidate_cache


@receiver(post_save)
@receiver(post_delete)
def invalidate_model_cache(sender, **kwargs):
    model_name = sender.__name__.lower()
    invalidate_cache(model_name)
