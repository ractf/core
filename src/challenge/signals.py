from django.core.cache import caches
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from challenge.models import Challenge, Category


@receiver([post_save, post_delete], sender=Challenge)
@receiver([post_save, post_delete], sender=Category)
def challenge_cache_invalidate(sender, instance, **kwargs):
    new_index = caches["default"].get("challenge_mod_index", 0) + 1
    caches["default"].set("challenge_mod_index", new_index)
