"""Signal receivers for the challenge app."""

from challenges.models import Category, Challenge, File, Tag
from challenges.views import get_cache_key
from django.core.cache import caches
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from hint.models import Hint, HintUse


@receiver([post_save, post_delete], sender=Challenge)
@receiver([post_save, post_delete], sender=Category)
@receiver([post_save, post_delete], sender=Hint)
@receiver([post_save, post_delete], sender=File)
@receiver([post_save, post_delete], sender=Tag)
def challenge_cache_invalidate(sender, instance, **kwargs):
    new_index = caches["default"].get("challenge_mod_index", 0) + 1
    caches["default"].set("challenge_mod_index", new_index, timeout=None)


@receiver([post_save, post_delete], sender=HintUse)
def team_cache_invalidate(sender, instance: HintUse, **kwargs):
    caches["default"].delete(get_cache_key(instance.user))
