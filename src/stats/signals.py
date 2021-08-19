from django.core.cache import cache
from django.db.models.signals import post_delete
from django.dispatch import receiver
from prometheus_client import Counter, Gauge

from backend.signals import (
    flag_score,
    register,
    team_create,
    websocket_connect,
    websocket_disconnect,
)
from challenge.models import Challenge, Solve
from member.models import Member
from team.models import Team

member_count = Gauge("member_count", "The number of members currently registered")
team_count = Gauge("team_count", "The number of teams currently registered")
attempts_total = Counter(
    "attempts_total",
    "Incorrect solves by challenge and category",
    labelnames=('challenge', 'category',),
)
solves_total = Counter(
    "solves_total",
    "Correct solves by challenge and category",
    labelnames=('challenge', 'category',),
)
points_total = Counter('points_total', "Total points scored")
connected_websocket_users = Gauge(
    "connected_websocket_users",
    "The number of users connected to the websocket",
    multiprocess_mode="livesum",
)

if not cache.get("migrations_needed"):
    cache.set("member_count", Member.objects.count(), timeout=None)
    member_count.set(cache.get("member_count"))

    cache.set("team_count", Team.objects.count(), timeout=None)
    team_count.set(cache.get("team_count"))


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
def on_solve_create(
    sender,
    user,
    team,
    challenge: Challenge,
    flag,
    solve: Solve,
    **kwargs,
) -> None:
    """Update challenge solve metrics."""

    labelset = dict(challenge=challenge.name, category=challenge.category.name)
    if solve.correct:
        solves_total.labels(**labelset).inc()
        points_total.inc(challenge.score)
    else:
        attempts_total.labels(**labelset).inc()


@receiver(post_delete, sender=Solve)
def on_solve_delete(sender, instance, **kwargs):
    # According to Dave, it does not make sense to delete a solve.
    # According to Joe, it does make sense in case someone breaks something.

    # We do not update the solve metrics here, as we use counters to
    # work around multiprocessing issues due to Python's limitation
    # of running on a single core. This also applies to the `points_total`
    # metric, which is not updated here either.
    pass


@receiver(websocket_connect)
def on_ws_connect(**kwargs):
    connected_websocket_users.inc()


@receiver(websocket_disconnect)
def on_ws_disconnect(**kwargs):
    connected_websocket_users.dec()
