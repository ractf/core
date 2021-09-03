"""Signal handlers for the sockets app."""

from asgiref.sync import async_to_sync
from challenges.models import Challenge
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from config import config
from core.signals import flag_reject, flag_score, team_join, use_hint
from sockets.models import Announcement
from sockets.serializers import AnnouncementSerializer


def get_team_channel(user):
    """Return the channel key of a user's team."""
    return f"team.{user.team.pk}"


def send(user, data):
    """Send a websocket message to a specific user's team."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(get_team_channel(user), data)


def broadcast(data):
    """Send a websocket message to all users."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)("event", data)


@receiver(flag_score)
def on_flag_score(user, team, challenge, flag, solve, **kwargs):
    """Broadcast a flag being scored."""
    # TODO: Frontend depends on this being sent
    # is there a way to either fix frontend or send this with less detail if solve broacast is off?
    # if not config.get("enable_solve_broadcast"):
    #     return
    broadcast(
        {
            "type": "send_json",
            "event_code": 1,
            "user": user.pk,
            "username": user.username,
            "challenge_id": challenge.pk,
            "challenge_name": challenge.name,
            "challenge_score": solve.score.points,
            "team": team.pk,
            "team_name": team.name,
        }
    )


@receiver(flag_reject)
def on_flag_reject(user, team, challenge, flag, **kwargs):
    """Tell a team about a flag being rejected."""
    send(
        user,
        {
            "type": "send_json",
            "event_code": 2,
            "user": user.pk,
            "username": user.username,
            "challenge_id": challenge.pk,
            "challenge_name": challenge.name,
            "team": team.pk,
            "team_name": team.name,
        },
    )


@receiver(use_hint)
def on_use_hint(user, team, hint, **kwargs):
    """Tell a team about a hint being used."""
    send(
        user,
        {
            "type": "send_json",
            "event_code": 3,
            "user": user.pk,
            "username": user.username,
            "team": team.pk,
            "team_name": team.name,
            "hint_name": hint.name,
            "hint_penalty": hint.penalty,
            "hint_text": hint.text,
            "challenge": hint.challenge.name,
        },
    )


@receiver(team_join)
def on_team_join(user, team, **kwargs):
    """Tell a team about a new member."""
    send(
        user,
        {
            "type": "send_json",
            "event_code": 4,
            "user": user.pk,
            "username": user.username,
            "team": team.pk,
            "team_name": team.name,
        },
    )


@receiver(post_save, sender=Announcement)
def on_announcement_create(sender, instance, **kwargs):
    """Broadcast a new announcement."""
    data = AnnouncementSerializer(instance).data
    data["type"] = "send_json"
    data["event_code"] = 5
    broadcast(data)


@receiver(post_save, sender=Challenge)
def on_challenge_edit(sender, instance, update_fields, **kwargs):
    """Broadcast a challenge modification."""
    if update_fields is not None and "first_blood" in update_fields:
        return
    broadcast({"type": "send_json", "event_code": 6, "challenge_id": instance.id})
