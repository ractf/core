import time

from django.core.cache import caches
from django.core.management import BaseCommand
from django.db import models
from django.db.models import Case, Prefetch, Value, When
from django.http import HttpRequest
from django.utils import timezone
from rest_framework.request import Request

from challenges import serializers
from challenges.models import Category, Challenge, File, Tag
from challenges.serializers import FastCategorySerializer
from challenges.sql import get_negative_votes, get_positive_votes, get_solve_counts
from config import config
from hint.models import Hint


def get_queryset():
    challenges = (
        Challenge.objects.annotate(
            unlock_time_surpassed=Case(
                When(release_time__lte=timezone.now(), then=Value(True)),
                default=Value(False),
                output_field=models.BooleanField(),
            )
        )
        .prefetch_related(
            Prefetch(
                "hint_set",
                queryset=Hint.objects.annotate(used=Value(False)),
                to_attr="hints",
            ),
            Prefetch("file_set", queryset=File.objects.all(), to_attr="files"),
            Prefetch(
                "tag_set",
                queryset=Tag.objects.all()
                if time.time() > config.get("end_time")
                else Tag.objects.filter(post_competition=False),
                to_attr="tags",
            ),
        )
        .select_related("first_blood")
    )
    categories = Category.objects.filter(release_time__lte=timezone.now())
    qs = categories.prefetch_related(Prefetch("category_challenges", queryset=challenges, to_attr="challenges"))
    return qs


def setup_context(context):
    context.update(
        {
            "request": Request(HttpRequest()),
            "solve_counter": get_solve_counts(),
            "votes_positive_counter": get_positive_votes(),
            "votes_negative_counter": get_negative_votes(),
            "solves": [],
        }
    )


def is_solved(challenge, *args, **kwargs):
    return False


def is_unlocked(challenge, *args, **kwargs):
    return challenge.unlock_requirements == ""


class Command(BaseCommand):
    help = "Creates a cache to lessen the impact of the first 15 seconds of request spam"

    def handle(self, *args, **options):
        categories = get_queryset()
        solve_counts = get_solve_counts()
        positive_votes = get_positive_votes()
        negative_votes = get_negative_votes()
        Challenge.is_unlocked = is_unlocked
        Challenge.is_solved = is_solved
        serializers.setup_context = setup_context

        categories = FastCategorySerializer(categories, many=True, context={}).data
        for category in categories:
            for challenge in category["challenges"]:
                challenge["votes"] = {
                    "positive": positive_votes.get(challenge["id"], 0),
                    "negative": negative_votes.get(challenge["id"], 0),
                }
                challenge["solve_count"] = solve_counts.get(challenge["id"], 0)
        caches["default"].set("preevent_cache", categories, timeout=None)
        print(categories)
