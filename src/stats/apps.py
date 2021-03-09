import sys

from django.apps import AppConfig, apps
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from prometheus_client import Gauge

from backend.signals import websocket_connect, websocket_disconnect


class StatsConfig(AppConfig):
    name = "stats"

    def ready(self):
        """Logic for adding extra prometheus statistics."""

        if "migrate" in sys.argv or "makemigrations" in sys.argv:
            # Don't run stats-related logic if we haven't migrated yet
            return

        # Pull relevant models from the other apps
        Team = apps.get_model("team", "Team")
        Member = apps.get_model("member", "Member")
        Solve = apps.get_model("challenge", "Solve")

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

        @receiver(post_save, sender=Member)
        def on_member_create(sender, instance, created, **kwargs):
            if created:
                member_count.inc()

        @receiver(post_delete, sender=Member)
        def on_member_delete(sender, instance, **kwargs):
            member_count.dec()

        @receiver(post_save, sender=Team)
        def on_team_create(sender, instance, created, **kwargs):
            if created:
                team_count.inc()

        @receiver(post_delete, sender=Team)
        def on_team_delete(sender, instance, **kwargs):
            team_count.dec()

        @receiver(post_save, sender=Solve)
        def on_solve_create(sender, instance, created, **kwargs):
            if created:
                solve_count.inc()
                if instance.correct:
                    correct_solve_count.inc()

        @receiver(post_delete, sender=Solve)
        def on_solve_delete(sender, instance, **kwargs):
            solve_count.dec()
            if instance.correct:
                correct_solve_count.dec()

        @receiver(websocket_connect)
        def on_ws_connect():
            connected_websocket_users.inc()

        @receiver(websocket_disconnect)
        def on_ws_disconnect():
            connected_websocket_users.dec()
