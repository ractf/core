from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from prometheus_client import Gauge

from backend.signals import websocket_disconnect, websocket_connect, team_create, flag_score, register
from challenge.models import Solve
from member.models import Member
from team.models import Team

member_count = Gauge("member_count", "The number of members currently registered")
member_count.set(Member.objects.count())

team_count = Gauge("team_count", "The number of teams currently registered")
team_count.set(Team.objects.count())

solve_count = Gauge("solve_count", "The count of both correct and incorrect solves")
solve_count.set(Solve.objects.count())

correct_solve_count = Gauge("correct_solve_count", "The count of correct solves")
correct_solve_count.set(Solve.objects.filter(correct=True).count())

connected_websocket_users = Gauge(
    "connected_websocket_users", "The number of users connected to the Websocket"
)


@receiver(register)
def on_member_create(sender, user, **kwargs):
    member_count.inc()


@receiver(post_delete, sender=Member)
def on_member_delete(sender, instance, **kwargs):
    member_count.dec()


@receiver(team_create)
def on_team_create(sender, team, **kwargs):
    team_count.inc()


@receiver(post_delete, sender=Team)
def on_team_delete(sender, instance, **kwargs):
    team_count.dec()


@receiver(flag_score)
def on_solve_create(sender, user, team, challenge, flag, solve, **kwargs):
    solve_count.inc()
    if solve.correct:
        correct_solve_count.inc()


@receiver(post_delete, sender=Solve)
def on_solve_delete(sender, instance, **kwargs):
    solve_count.dec()
    if instance.correct:
        correct_solve_count.dec()


@receiver(websocket_connect)
def on_ws_connect(**kwargs):
    connected_websocket_users.inc()


@receiver(websocket_disconnect)
def on_ws_disconnect(**kwargs):
    connected_websocket_users.dec()
