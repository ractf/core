from django.db.models.signals import post_save
from django.dispatch import receiver

from challenge.models import Solve
from achievements.models import Achievement, UserAchievement
from plugins import plugins


@receiver(post_save, sender=Solve)
def on_score(sender, instance, **kwargs):
    for achievement in Achievement.objects.all():
        if UserAchievement.objects.filter(user=instance.solved_by, achievement=achievement, earned=True).exists():
            continue

        plugin = plugins.plugins['achievement'][achievement.type](achievement)

        earned = plugin.check_completed(instance)

        try:
            user_achievement = UserAchievement.objects.get(user=instance.solved_by, achievement=achievement)
        except UserAchievement.DoesNotExist:
            user_achievement = UserAchievement(user=instance.solved_by, achievement=achievement)
        user_achievement.earned = earned
        user_achievement.progress = plugin.check_progress(instance)
        user_achievement.save()
