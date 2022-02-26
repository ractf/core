import hashlib
import time
from contextlib import suppress
from typing import Union

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.db import models, transaction
from django.db.models import Case, Prefetch, Sum, Value, When
from django.utils import timezone
from rest_framework import permissions
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from backend.permissions import AdminOrReadOnly, IsBot, ReadOnlyBot
from backend.response import FormattedResponse
from backend.signals import flag_reject, flag_score, flag_submit
from backend.viewsets import AdminCreateModelViewSet
from challenge.models import (
    Category,
    Challenge,
    ChallengeFeedback,
    ChallengeVote,
    File,
    Score,
    Solve,
    Tag,
)
from challenge.permissions import CompetitionOpen
from challenge.serializers import (
    AdminScoreSerializer,
    ChallengeFeedbackSerializer,
    CreateCategorySerializer,
    CreateChallengeSerializer,
    FastAdminCategorySerializer,
    FastAdminChallengeSerializer,
    FastCategorySerializer,
    FastChallengeSerializer,
    FileSerializer,
    TagSerializer,
    get_negative_votes,
    get_positive_votes,
    get_solve_counts,
)
from config import config
from hint.models import Hint, HintUse
from sockets.signals import broadcast
from team.models import Team
from team.permissions import HasTeam


def get_cache_key(user):
    if user.team is None:
        return str(caches["default"].get("challenge_mod_index", 0)) + "categoryvs_no_team"
    else:
        return str(caches["default"].get("challenge_mod_index", 0)) + "categoryvs_team_" + str(user.team.id)


class CategoryViewset(AdminCreateModelViewSet):
    queryset = Category.objects.all()
    permission_classes = (CompetitionOpen & AdminOrReadOnly,)
    throttle_scope = "challenges"
    pagination_class = None
    serializer_class = FastCategorySerializer
    admin_serializer_class = FastAdminCategorySerializer
    create_serializer_class = CreateCategorySerializer

    def get_queryset(self):
        if self.request.user.is_staff and self.request.user.should_deny_admin():
            return Category.objects.none()
        team = self.request.user.team
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
                    queryset=Hint.objects.annotate(
                        used=Case(
                            When(id__in=HintUse.objects.filter(team=team).values_list("hint_id"), then=Value(True)),
                            default=Value(False),
                            output_field=models.BooleanField(),
                        )
                    ),
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
                "hint_set__uses",
            )
            .select_related("first_blood")
        )
        if self.request.user.is_staff:
            categories = Category.objects
        else:
            categories = Category.objects.filter(release_time__lte=timezone.now())
        qs = categories.prefetch_related(Prefetch("category_challenges", queryset=challenges, to_attr="challenges"))
        return qs

    def list(self, request, *args, **kwargs):
        cache = caches["default"]
        if (
            config.get("enable_preevent_cache")
            and config.get("start_time") + 15 > time.time()
            and "preevent_cache" in cache
            and not request.user.is_staff
        ):
            return FormattedResponse(cache.get("preevent_cache"))

        categories = cache.get(get_cache_key(request.user))
        if categories is None or not config.get("enable_caching"):
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            categories = serializer.data
            cache.set(get_cache_key(request.user), categories, 3600)

        solve_counts = get_solve_counts()
        positive_votes = get_positive_votes()
        negative_votes = get_negative_votes()
        for category in categories:
            for challenge in category["challenges"]:
                challenge["votes"] = {
                    "positive": positive_votes.get(challenge["id"], 0),
                    "negative": negative_votes.get(challenge["id"], 0),
                }
                challenge["solve_count"] = solve_counts.get(challenge["id"], 0)

        return FormattedResponse(categories)


class ChallengeViewset(AdminCreateModelViewSet):
    queryset = Challenge.objects.all()
    permission_classes = (CompetitionOpen & AdminOrReadOnly,)
    throttle_scope = "challenges"
    pagination_class = None
    serializer_class = FastChallengeSerializer
    admin_serializer_class = FastAdminChallengeSerializer
    create_serializer_class = CreateChallengeSerializer

    def get_queryset(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return self.queryset
        return Challenge.get_unlocked_annotated_queryset(self.request.user)


class ScoresViewset(ModelViewSet):
    queryset = Score.objects.all()
    permission_classes = (IsAdminUser,)
    serializer_class = AdminScoreSerializer

    def recalculate_scores(self, user, team):
        if user:
            user = get_object_or_404(get_user_model(), id=user)
            user.leaderboard_points = (
                Score.objects.filter(user=user, leaderboard=True).aggregate(Sum("points"))["points__sum"] or 0
            )
            user.points = Score.objects.filter(user=user).aggregate(Sum("points"))["points__sum"] or 0
            user.last_score = (
                Score.objects.filter(user=user, leaderboard=True, tiebreaker=True)
                .order_by("timestamp")
                .first()
                .timestamp
            )
            user.save()
        if team:
            team = get_object_or_404(Team, id=team)
            team.leaderboard_points = (
                Score.objects.filter(team=team, leaderboard=True).aggregate(Sum("points"))["points__sum"] or 0
            )
            team.points = Score.objects.filter(team=team).aggregate(Sum("points"))["points__sum"] or 0
            team.last_score = (
                Score.objects.filter(team=team, leaderboard=True, tiebreaker=True)
                .order_by("timestamp")
                .first()
                .timestamp
            )
            team.save()

    def create(self, req, *args, **kwargs):
        x = super().create(req, *args, **kwargs)
        self.recalculate_scores(req.data.get("user", None), req.data.get("team", None))
        return x

    def update(self, req, *args, **kwargs):
        x = super().update(req, *args, **kwargs)
        self.recalculate_scores(req.data.get("user", None), req.data.get("team", None))
        return x

    def partial_update(self, req, *args, **kwargs):
        x = super().partial_update(req, *args, **kwargs)
        self.recalculate_scores(req.data.get("user", None), req.data.get("team", None))
        return x

    def destroy(self, req, *args, **kwargs):
        x = super().destroy(req, *args, **kwargs)
        self.recalculate_scores(req.data.get("user", None), req.data.get("team", None))
        return x


class ChallengeFeedbackView(APIView):
    permission_classes = (IsAuthenticated & HasTeam & ReadOnlyBot,)

    def get(self, request):
        challenge = get_object_or_404(Challenge, id=request.data.get("challenge"))
        feedback = ChallengeFeedback.objects.filter(challenge=challenge)
        if request.user.is_staff:
            return FormattedResponse(ChallengeFeedbackSerializer(feedback, many=True).data)
        return FormattedResponse(ChallengeFeedbackSerializer(feedback.filter(user=request.user).first()).data)

    def post(self, request):
        challenge = get_object_or_404(Challenge, id=request.data.get("challenge"))
        solve_set = Solve.objects.filter(challenge=challenge)

        if not solve_set.filter(team=request.user.team, correct=True).exists():
            return FormattedResponse(m="challenge_not_solved", status=HTTP_403_FORBIDDEN)

        current_feedback = ChallengeFeedback.objects.filter(user=request.user, challenge=challenge)
        if current_feedback.exists():
            current_feedback.delete()

        ChallengeFeedback(user=request.user, challenge=challenge, feedback=request.data.get("feedback")).save()
        return FormattedResponse(m="feedback_recorded")


class ChallengeVoteView(APIView):
    permission_classes = (IsAuthenticated & HasTeam & ~IsBot,)

    def post(self, request):
        challenge = get_object_or_404(Challenge, id=request.data.get("challenge"))
        solve_set = Solve.objects.filter(challenge=challenge)

        if not solve_set.filter(team=request.user.team, correct=True).exists():
            return FormattedResponse(m="challenge_not_solved", status=HTTP_403_FORBIDDEN)

        current_vote = ChallengeVote.objects.filter(user=request.user, challenge=challenge)
        if current_vote.exists():
            current_vote.delete()

        ChallengeVote(user=request.user, challenge=challenge, positive=request.data.get("positive")).save()
        return FormattedResponse(m="vote_recorded")


class FlagSubmitView(APIView):
    permission_classes = (CompetitionOpen & IsAuthenticated & HasTeam & ~IsBot,)
    throttle_scope = "flag_submit"

    def post(self, request):
        if not config.get("enable_flag_submission") or (
            not config.get("enable_flag_submission_after_competition") and time.time() > config.get("end_time")
        ):
            return FormattedResponse(m="flag_submission_disabled", status=HTTP_403_FORBIDDEN)

        with transaction.atomic():
            team = Team.objects.select_for_update().get(id=request.user.team.id)
            user = get_user_model().objects.select_for_update().get(id=request.user.id)
            flag = request.data.get("flag")
            challenge_id = request.data.get("challenge")
            if not flag or not challenge_id:
                return FormattedResponse(status=HTTP_400_BAD_REQUEST, m="No flag or challenge ID provided")

            challenge = get_object_or_404(Challenge.objects.select_for_update(), id=challenge_id)
            solve_set = Solve.objects.filter(challenge=challenge)
            if solve_set.filter(team=team, correct=True).exists():
                return FormattedResponse(m="already_solved_challenge", status=HTTP_403_FORBIDDEN)
            if not challenge.is_unlocked(user):
                return FormattedResponse(m="challenge_not_unlocked", status=HTTP_403_FORBIDDEN)

            if challenge.challenge_metadata.get("attempt_limit"):
                count = solve_set.filter(team=team).count()
                if count > challenge.challenge_metadata["attempt_limit"]:
                    flag_reject.send(
                        sender=self.__class__,
                        user=user,
                        team=team,
                        challenge=challenge,
                        flag=flag,
                        reason="attempt_limit_reached",
                    )
                    return FormattedResponse(d={"correct": False}, m="attempt_limit_reached")

            flag_submit.send(sender=self.__class__, user=user, team=team, challenge=challenge, flag=flag)

            if not challenge.flag_plugin.check(flag, user=user, team=team):
                flag_reject.send(
                    sender=self.__class__, user=user, team=team, challenge=challenge, flag=flag, reason="incorrect_flag"
                )
                challenge.points_plugin.register_incorrect_attempt(user, team, flag, solve_set)
                return FormattedResponse(d={"correct": False}, m="incorrect_flag")

            solve = challenge.points_plugin.score(user, team, flag, solve_set.filter(correct=True))

            if challenge.needs_recalculate:
                challenge.recalculate_score(solve_set)
                broadcast({
                    "type": "send_json",
                    "event_code": 7,
                    "challenge_id": challenge.id,
                    "challenge_score": solve.score.points,
                })

            if challenge.first_blood is None:
                challenge.first_blood = user
                challenge.save(update_fields=["first_blood"])
                hook = config.get("firstblood_webhook")
                if hook and hook != "":
                    challenge_clean = challenge.name.replace("`", "").replace("@", "@\u200b")
                    team_clean = team.name.replace("`", "").replace("@", "@\u200b")
                    if "discord.com" in hook and not hook.endswith("/slack"):
                        hook += "/slack"
                    challenge_clean = challenge_clean.replace("@", "@\u200b")
                    team_clean = team_clean.replace("@", "@\u200b")
                    body = {
                        "username": "First Bloods",
                        "attachments": [
                            {
                                "title": f":drop_of_blood: First Blood on `{challenge_clean}`!",
                                "text": f"By team `{team_clean}`",
                                "color": "#ff0000",
                            }
                        ],
                    }

                    with suppress(requests.exceptions.RequestException):
                        requests.post(hook, json=body)

            user.save()
            team.save()
            flag_score.send(sender=self.__class__, user=user, team=team, challenge=challenge, flag=flag, solve=solve)
            caches["default"].delete(get_cache_key(request.user))
            ret = {"correct": True}
            if challenge.post_score_explanation:
                ret["explanation"] = challenge.post_score_explanation
            return FormattedResponse(d=ret, m="correct_flag")


class FlagCheckView(APIView):
    permission_classes = (CompetitionOpen & IsAuthenticated & HasTeam & ~IsBot,)
    throttle_scope = "flag_submit"

    def post(self, request):
        if not config.get("enable_flag_submission") or (
            not config.get("enable_flag_submission_after_competition") and time.time() > config.get("end_time")
        ):
            return FormattedResponse(m="flag_submission_disabled", status=HTTP_403_FORBIDDEN)
        team = Team.objects.get(id=request.user.team.id)
        user = get_user_model().objects.get(id=request.user.id)
        flag = request.data.get("flag")
        challenge_id = request.data.get("challenge")
        if not flag or not challenge_id:
            return FormattedResponse(status=HTTP_400_BAD_REQUEST)

        challenge = get_object_or_404(Challenge.objects.select_for_update(), id=challenge_id)
        solve_set = Solve.objects.filter(challenge=challenge)
        if not solve_set.filter(team=team, correct=True).exists():
            return FormattedResponse(m="havent_solved_challenge", status=HTTP_403_FORBIDDEN)

        if not challenge.flag_plugin.check(flag, user=user, team=team):
            return FormattedResponse(d={"correct": False}, m="incorrect_flag")

        ret = {"correct": True}

        if challenge.post_score_explanation:
            ret["explanation"] = challenge.post_score_explanation
        return FormattedResponse(d=ret, m="correct_flag")


class FileViewSet(ModelViewSet):
    queryset = File.objects.all()
    permission_classes = (IsAdminUser,)
    parser_classes = (MultiPartParser,)
    throttle_scope = "file"
    serializer_class = FileSerializer
    pagination_class = None

    def create(self, request: Request, *args, **kwargs) -> Union[FormattedResponse, Response]:
        """Create a File, given a URL or from a direct upload."""
        challenge = get_object_or_404(Challenge, id=request.data.get("challenge"))
        file_url, file_data, file_size, file_digest, file_name = (
            request.data.get(name) for name in ("url", "upload", "size", "md5", "name")
        )

        if not file_url and not file_data:
            return FormattedResponse(m="Either url or upload must be provided.", status=HTTP_400_BAD_REQUEST)

        if file_data:
            if len(file_data) > settings.MAX_UPLOAD_SIZE:
                return FormattedResponse(
                    m=f"File cannot be over {settings.MAX_UPLOAD_SIZE} bytes in size.", status=HTTP_400_BAD_REQUEST
                )
            file = File(challenge=challenge, upload=file_data)
            file.name = file.upload.name
            file.size = file.upload.size

            md5 = hashlib.md5()
            for chunk in file_data.chunks():
                md5.update(chunk)
            file.md5 = md5.hexdigest()

            file.save()
            if settings.DOMAIN and not settings.USE_AWS_S3_FILE_STORAGE:
                file.url = f"https://{settings.DOMAIN}{file.upload.url}"
            else:
                file.url = file.upload.url  # This field isn't set properly until saving
        else:
            file = File(challenge=challenge, url=file_url, size=file_size, md5=file_digest, name=file_name)

        file.save()
        return FormattedResponse(self.serializer_class(file).data)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """If the file was uploaded, delete the FileField on the model first."""
        file: File = self.get_object()
        if file.upload:
            file.upload.delete(save=False)
        return super().destroy(request, *args, **kwargs)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    permission_classes = (IsAdminUser,)
    throttle_scope = "tag"
    serializer_class = TagSerializer
    pagination_class = None
