"""Signal receivers for the challenge app."""

from challenge.models import Challenge
from django.core.cache import caches
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Challenge)
def challenge_save(sender, instance, **kwargs):
    """Update the challenge modification index when a challenge is modified."""
    new_index = caches["default"].get("challenge_mod_index", 0) + 1
    caches["default"].set("challenge_mod_index", new_index)
