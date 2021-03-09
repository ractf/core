from django.apps import AppConfig
from django.db.models.signals import post_save
from django.dispatch import receiver

from prometheus_client import Gauge


class StatsConfig(AppConfig):
    name = "stats"

    def ready(self):
        from member.models import Member
        from team.models import Team
        from challenge.models import Solve

        member_count = Gauge("member_count", "The number of members currently registered")
        member_count.set(Member.objects.count())

        team_count = Gauge("team_count", "The number of teams currently registered")
        team_count.set(Team.objects.count())

        solve_count = Gauge("solve_count", "The count of both correct and incorrect solves")
        solve_count.set(Solve.objects.count())

        correct_solve_count = Gauge("correct_solve_count", "The count of correct solves")
        correct_solve_count.set(Solve.objects.filter(correct=True).count())

        @receiver(post_save, sender=Member)
        def on_member_create(sender, instance, created, **kwargs):
            if created:
                member_count.inc()

        @receiver(post_save, sender=Team)
        def on_team_create(sender, instance, created, **kwargs):
            if created:
                team_count.inc()

        @receiver(post_save, sender=Solve)
        def on_solve_create(sender, instance, created, **kwargs):
            if created:
                solve_count.inc()
                if instance.correct:
                    correct_solve_count.inc()