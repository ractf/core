from django.core.cache import caches
from django.dispatch import receiver
from django.db.models.signals import post_delete

from backend.signals import websocket_disconnect, websocket_connect, team_create, flag_score, register
from challenge.models import Solve
from member.models import Member
from team.models import Team

cache = caches["default"]

# When the worker starts up, set these in the cache to stay in sync
cache.set("prom_member_count", Member.objects.count(), timeout=None)
cache.set("prom_team_count", Team.objects.count(), timeout=None)
cache.set("prom_solve_count", Solve.objects.count(), timeout=None)
cache.set("prom_correct_solve_count", Solve.objects.filter(correct=True).count(), timeout=None)
cache.set("prom_connected_websocket_users", 0, timeout=None)


@receiver(register)
def on_member_create(sender, user, **kwargs):
    cache.set("prom_member_count", cache.get("prom_member_count") + 1, timeout=None)


@receiver(post_delete, sender=Member)
def on_member_delete(sender, instance, **kwargs):
    cache.set("prom_member_count", cache.get("prom_member_count") - 1, timeout=None)


@receiver(team_create)
def on_team_create(sender, team, **kwargs):
    cache.set("prom_team_count", cache.get("prom_team_count") + 1, timeout=None)


@receiver(post_delete, sender=Team)
def on_team_delete(sender, instance, **kwargs):
    cache.set("prom_team_count", cache.get("prom_team_count") - 1, timeout=None)


@receiver(flag_score)
def on_solve_create(sender, user, team, challenge, flag, solve, **kwargs):
    cache.set("prom_solve_count", cache.get("prom_solve_count") + 1, timeout=None)
    if solve.correct:
        cache.set("prom_correct_solve_count", cache.get("prom_correct_solve_count") + 1, timeout=None)


@receiver(post_delete, sender=Solve)
def on_solve_delete(sender, instance, **kwargs):
    cache.set("prom_solve_count", cache.get("prom_solve_count") - 1, timeout=None)
    if instance.correct:
        cache.set("prom_correct_solve_count", cache.get("prom_correct_solve_count") - 1, timeout=None)


@receiver(websocket_connect)
def on_ws_connect(**kwargs):
    cache.set("prom_connected_websocket_users", cache.get("prom_connected_websocket_users") + 1, timeout=None)


@receiver(websocket_disconnect)
def on_ws_disconnect(**kwargs):
    cache.set("prom_connected_websocket_users", cache.get("prom_connected_websocket_users") - 1, timeout=None)
