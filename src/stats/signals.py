from django.core.cache import cache
from django.dispatch import receiver
from django.db.models.signals import post_delete
from prometheus_client import Gauge

from backend.signals import websocket_disconnect, websocket_connect, team_create, flag_score, register
from challenge.models import Solve
from member.models import Member
from team.models import Team

# When the worker starts up, set these in the cache to stay in sync
cache.set("member_count", Member.objects.count(), timeout=None)
cache.set("team_count", Team.objects.count(), timeout=None)
cache.set("solve_count", Solve.objects.count(), timeout=None)
cache.set("correct_solve_count", Solve.objects.filter(correct=True).count(), timeout=None)

connected_websocket_users = Gauge(
    "connected_websocket_users",
    "The number of users connected to the websocket",
    multiprocess_mode="livesum"
)


@receiver(register)
def on_member_create(sender, user, **kwargs):
    cache.set("member_count", cache.get("member_count") + 1, timeout=None)


@receiver(post_delete, sender=Member)
def on_member_delete(sender, instance, **kwargs):
    cache.set("member_count", cache.get("member_count") - 1, timeout=None)


@receiver(team_create)
def on_team_create(sender, team, **kwargs):
    cache.set("team_count", cache.get("team_count") + 1, timeout=None)


@receiver(post_delete, sender=Team)
def on_team_delete(sender, instance, **kwargs):
    cache.set("team_count", cache.get("team_count") - 1, timeout=None)


@receiver(flag_score)
def on_solve_create(sender, user, team, challenge, flag, solve, **kwargs):
    cache.set("solve_count", cache.get("solve_count") + 1, timeout=None)
    if solve.correct:
        cache.set("correct_solve_count", cache.get("correct_solve_count") + 1, timeout=None)


@receiver(post_delete, sender=Solve)
def on_solve_delete(sender, instance, **kwargs):
    cache.set("solve_count", cache.get("solve_count") - 1, timeout=None)
    if instance.correct:
        cache.set("correct_solve_count", cache.get("correct_solve_count") - 1, timeout=None)


@receiver(websocket_connect)
def on_ws_connect(**kwargs):
    connected_websocket_users.inc()


@receiver(websocket_disconnect)
def on_ws_disconnect(**kwargs):
    connected_websocket_users.dec()
