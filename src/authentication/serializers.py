import secrets
import time

from django.conf import settings
from django.contrib.auth import get_user_model, password_validation
from django.utils import timezone
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)

from authentication.models import InviteCode, PasswordResetToken
from backend.exceptions import FormattedException
from backend.mail import send_email
from backend.signals import register
from config import config
from plugins import providers
from team.models import Team


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)

    def validate(self, data):
        user = providers.get_provider("login").login_user(**data, context=self.context)
        data["user"] = user
        return data


class LoginTwoFactorSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)
    tfa = serializers.CharField(max_length=255, allow_null=True, allow_blank=True)

    def validate(self, data):
        user = providers.get_provider("login").login_user(**data, context=self.context)
        data["user"] = user
        return data


class RegistrationSerializer(serializers.Serializer):
    def validate(self, _):
        register_end_time = config.get("register_end_time")
        if not (config.get("enable_registration") and time.time() >= config.get("register_start_time")) and (register_end_time < 0 or register_end_time > time.time()):
            raise FormattedException(m="registration_not_open", status=HTTP_403_FORBIDDEN)

        validated_data = providers.get_provider("registration").validate(self.initial_data)
        if config.get("invite_required"):
            if not self.initial_data.get("invite", None):
                raise FormattedException(m="invite_required", status=HTTP_400_BAD_REQUEST)
            validated_data["invite"] = self.initial_data["invite"]
        return validated_data

    def create(self, validated_data):
        user = providers.get_provider("registration").register_user(**validated_data, context=self.context)

        if not get_user_model().objects.all().exists():
            user.is_staff = True
            user.is_superuser = True

        invite_code = None
        if config.get("invite_required"):
            if InviteCode.objects.filter(code=validated_data["invite"]):
                invite_code = InviteCode.objects.get(code=validated_data["invite"])
                if invite_code.uses >= invite_code.max_uses:
                    raise FormattedException(m="invite_already_used", status=HTTP_403_FORBIDDEN)
            else:
                raise FormattedException(m="invalid_invite", status=HTTP_403_FORBIDDEN)

        if not settings.MAIL["SEND"]:
            user.email_verified = True
            user.is_visible = True
        else:
            user.save()
            try:
                send_email(user.email, "RACTF - Verify your email", "verify", url=settings.FRONTEND_URL + "verify?id={}&secret={}".format(user.id, user.email_token))
            except:
                user.delete()
                raise FormattedException(m="creation_failed")

        if invite_code:
            invite_code.uses += 1
            if invite_code.uses >= invite_code.max_uses:
                invite_code.fully_used = True
            invite_code.save()
            if invite_code.auto_team:
                user.team = invite_code.auto_team

        if not config.get("enable_teams"):
            user.save()
            user.team = Team.objects.create(
                owner=user,
                name=user.username,
                password=secrets.token_hex(32),
            )

        user.save()

        register.send(sender=self.__class__, user=user)

        if not settings.MAIL["SEND"]:
            return {"token": user.issue_token(), "email": user.email}
        else:
            return {}

    def to_representation(self, instance):
        representation = super(RegistrationSerializer, self).to_representation(instance)
        representation.pop("password", None)
        return representation


class PasswordResetSerializer(serializers.Serializer):
    uid = serializers.IntegerField()
    token = serializers.CharField(max_length=128)
    password = serializers.CharField()

    def validate(self, data):
        uid = data.get("uid")
        token = data.get("token")
        password = data.get("password")
        user = get_object_or_404(get_user_model(), id=uid)
        reset_token = get_object_or_404(PasswordResetToken, token=token, user_id=uid, expires__gt=timezone.now())
        password_validation.validate_password(password, reset_token)
        data["user"] = user
        data["reset_token"] = reset_token
        return data


class EmailVerificationSerializer(serializers.Serializer):
    uid = serializers.IntegerField()
    token = serializers.CharField(max_length=64)

    def validate(self, data):
        uid = int(data.get("uid"))
        token = data.get("token")
        user = get_object_or_404(get_user_model(), id=uid, email_token=token)
        if user.email_verified:
            raise FormattedException(m="email_already_verified", status=HTTP_403_FORBIDDEN)
        data["user"] = user
        return data


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        user = get_object_or_404(get_user_model(), email=data.get("email"))
        if user.email_verified:
            raise FormattedException(m="email_already_verified", status=HTTP_403_FORBIDDEN)
        data["user"] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    old_password = serializers.CharField()

    def validate(self, data):
        user = self.context["request"].user
        password = data.get("password")
        old_password = data.get("old_password")
        if not user.check_password(old_password):
            raise FormattedException(status=HTTP_401_UNAUTHORIZED, m="invalid_password")
        password_validation.validate_password(password, user)
        return data


class GenerateInvitesSerializer(serializers.Serializer):
    amount = serializers.IntegerField(max_value=10000)
    max_uses = serializers.IntegerField(required=False, default=1)
    auto_team = serializers.IntegerField(required=False, default=None)


class InviteCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteCode
        fields = ["id", "code", "uses", "max_uses", "auto_team"]


class CreateBotSerializer(serializers.Serializer):
    username = serializers.CharField()
    is_visible = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()
