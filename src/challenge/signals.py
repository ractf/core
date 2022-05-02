from django.core.cache import caches
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from challenge.models import Category, Challenge, File, Score, Tag
from challenge.views import get_cache_key
from hint.models import Hint, HintUse
from scorerecalculator.views import recalculate_team


@receiver([post_save, post_delete], sender=Challenge)
@receiver([post_save, post_delete], sender=Category)
@receiver([post_save, post_delete], sender=Hint)
@receiver([post_save, post_delete], sender=File)
@receiver([post_save, post_delete], sender=Tag)
def challenge_cache_invalidate(sender, instance, **kwargs):
    new_index = caches["default"].get("challenge_mod_index", 0) + 1
    caches["default"].set("challenge_mod_index", new_index, timeout=None)


@receiver([post_save], sender=Challenge)
def challenge_recalculate(sender, instance, **kwargs):
    with transaction.atomic():
        correct_solves = instance.solves.filter(correct=True, revoked=False)
        if instance.current_score is None:
            Score.objects.filter(id__in=correct_solves.values_list("score", flat=True)).update(points=instance.score)
            for solve in correct_solves:
                recalculate_team(solve.team)
        else:
            Score.objects.filter(id__in=correct_solves.values_list("score", flat=True))\
                .update(points=instance.current_score)
            for solve in correct_solves:
                recalculate_team(solve.team)


@receiver([post_save, post_delete], sender=HintUse)
def team_cache_invalidate(sender, instance: HintUse, **kwargs):
    caches["default"].delete(get_cache_key(instance.user))
