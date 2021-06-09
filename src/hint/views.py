from django.core.cache import caches
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_403_FORBIDDEN
from rest_framework.views import APIView

from challenge.permissions import CompetitionOpen
from challenge.views import get_cache_key
from core.permissions import IsBot
from core.response import FormattedResponse
from core.signals import use_hint
from core.viewsets import AdminCreateModelViewSet
from hint.models import Hint, HintUse
from hint.permissions import HasUsedHint
from hint.serializers import (
    CreateHintSerializer,
    FullHintSerializer,
    HintSerializer,
    UseHintSerializer,
)
from team.permissions import HasTeam


class HintViewSet(AdminCreateModelViewSet):
    queryset = Hint.objects.all()
    permission_classes = (HasUsedHint,)
    throttle_scope = "hint"
    pagination_class = None
    serializer_class = HintSerializer
    admin_serializer_class = FullHintSerializer
    create_serializer_class = CreateHintSerializer


class UseHintView(APIView):
    permission_classes = (CompetitionOpen & IsAuthenticated & HasTeam & ~IsBot,)
    throttle_scope = "use_hint"

    def post(self, request):
        serializer = UseHintSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hint_id = serializer.validated_data["id"]
        hint = get_object_or_404(Hint, id=hint_id)
        if not hint.challenge.is_unlocked(request.user):
            return FormattedResponse(m="challenge_not_unlocked", s=False, status=HTTP_403_FORBIDDEN)
        if HintUse.objects.filter(hint=hint, team=request.user.team).exists():
            return FormattedResponse(m="hint_already_used", s=False, status=HTTP_403_FORBIDDEN)
        use_hint.send(sender=self.__class__, user=request.user, team=request.user.team, hint=hint)
        HintUse(
            hint=hint,
            team=request.user.team,
            user=request.user,
            challenge=hint.challenge,
        ).save()
        serializer = FullHintSerializer(hint, context={"request": request})
        caches["default"].delete(get_cache_key(request.user))
        return FormattedResponse(d=serializer.data)
