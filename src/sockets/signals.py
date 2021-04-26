from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from announcements.models import Announcement
from announcements.serializers import AnnouncementSerializer
from backend.signals import flag_score, flag_reject, use_hint, team_join
from challenge.models import Challenge
from config import config


def get_team_channel(user):
    return f'team.{user.team.id}'


def send(user, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(get_team_channel(user), data)


def broadcast(data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)('event', data)


@receiver(flag_score)
def on_flag_score(user, team, challenge, flag, solve, **kwargs):
    if not config.get('enable_solve_broadcast'):
        return
    broadcast({
        'type': 'send_json',
        'event_code': 1,
        'user': user.id,
        'username': user.username,
        'challenge_id': challenge.id,
        'challenge_name': challenge.name,
        'challenge_score': solve.score.points,
        'team': team.id,
        'team_name': team.name,
    })


@receiver(flag_reject)
def on_flag_reject(user, team, challenge, flag, **kwargs):
    send(user, {
        'type': 'send_json',
        'event_code': 2,
        'user': user.id,
        'username': user.username,
        'challenge_id': challenge.id,
        'challenge_name': challenge.name,
        'team': team.id,
        'team_name': team.name,
    })


@receiver(use_hint)
def on_use_hint(user, team, hint, **kwargs):
    send(user, {
        'type': 'send_json',
        'event_code': 3,
        'user': user.id,
        'username': user.username,
        'team': team.id,
        'team_name': team.name,
        'hint_name': hint.name,
        'hint_penalty': hint.penalty,
        'hint_text': hint.text,
        'challenge': hint.challenge.name,
    })


@receiver(team_join)
def on_team_join(user, team, **kwargs):
    send(user, {
        'type': 'send_json',
        'event_code': 4,
        'user': user.id,
        'username': user.username,
        'team': team.id,
        'team_name': team.name,
    })


@receiver(post_save, sender=Announcement)
def on_announcement_create(sender, instance, **kwargs):
    data = AnnouncementSerializer(instance).data
    data['type'] = 'send_json'
    data['event_code'] = 5
    broadcast(data)


@receiver(post_save, sender=Challenge)
def on_challenge_edit(sender, instance, **kwargs):
    broadcast({
        "type": "send_json",
        "event_code": 6,
        "challenge_id": instance.id
    })
