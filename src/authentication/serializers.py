"""Serializers used for the authentication app."""

import secrets
import time
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth import password_validation
from django.utils import timezone
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)

from authentication.models import InviteCode, PasswordResetToken
from config import config
from core import providers
from core.exceptions import FormattedException
from core.mail import send_email
from core.signals import register
from teams.models import Team, Member


class LoginSerializer(serializers.Serializer):
    """Serialize fields used in the login form."""

    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)

    def validate(self, data):
        """Validate data used in the login form."""
        user = providers.get_provider("login").login_user(**data, context=self.context)
        data["user"] = user
        return data


class LoginTwoFactorSerializer(serializers.Serializer):
    """Serialize fields used in a login for 2FA-enabled accounts."""

    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)
    tfa = serializers.CharField(max_length=255, allow_null=True, allow_blank=True)

    def validate(self, data):
        """Validate data using the relevant provider for this user."""
        user = providers.get_provider("login").login_user(**data, context=self.context)
        data["user"] = user
        return data


class RegistrationSerializer(serializers.Serializer):
    """Serialize fields used for registering new accounts."""

    def validate(self, _):
        """Validate relevant fields for a new account's field data."""
        register_end_time = config.get("register_end_time")
        if not (config.get("enable_registration") and time.time() >= config.get("register_start_time")) and (
            register_end_time < 0 or register_end_time > time.time()
        ):
            raise FormattedException(m="registration_not_open", status=HTTP_403_FORBIDDEN)

        validated_data = providers.get_provider("registration").validate(self.initial_data)
        if config.get("invite_required"):
            if not self.initial_data.get("invite", None):
                raise FormattedException(m="invite_required", status=HTTP_400_BAD_REQUEST)
            validated_data["invite"] = self.initial_data["invite"]
        return validated_data

    def create(self, validated_data):
        """Create a user, given all the relevant form fields."""
        user = providers.get_provider("registration").register_user(**validated_data, context=self.context)

        if not Member.objects.all().exists():
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
                send_email(
                    user.email,
                    f"{config.get('event_name')} - Verify your email",
                    "verify",
                    url=settings.FRONTEND_URL + "verify?id={}&secret={}".format(user.pk, user.email_token),
                    event_name=config.get("event_name"),
                )
            except SMTPException:
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
        """Get a dictionary representation of this serializer's data."""
        representation = super(RegistrationSerializer, self).to_representation(instance)
        representation.pop("password", None)
        return representation


class PasswordResetSerializer(serializers.Serializer):
    """Serialize fields used for resetting a user's data."""

    uid = serializers.IntegerField()
    token = serializers.CharField(max_length=128)
    password = serializers.CharField()

    def validate(self, data):
        """Validate and return data sent for a password reset request."""
        uid = data.get("uid")
        token = data.get("token")
        password = data.get("password")
        user = get_object_or_404(Member, pk=uid)
        reset_token = get_object_or_404(PasswordResetToken, token=token, user_id=uid, expires__gt=timezone.now())
        password_validation.validate_password(password, reset_token)
        data["user"] = user
        data["reset_token"] = reset_token
        return data


class EmailVerificationSerializer(serializers.Serializer):
    """Serialize fields used for verifying an account by email."""

    uid = serializers.IntegerField()
    token = serializers.CharField(max_length=64)

    def validate(self, data):
        """Validate the user ID and token, raising an error if the user is already verified."""
        uid = int(data.get("uid"))
        token = data.get("token")
        user = get_object_or_404(Member, id=uid, email_token=token)
        if user.email_verified:
            raise serializers.ValidationError("email is already verified")
        data["user"] = user
        return data


class ResendEmailSerializer(serializers.Serializer):
    """Serialize fields used for resending a verification email to a user."""

    email = serializers.EmailField()

    def validate(self, data):
        """Validate the provided email, ensuring that it links to a real user."""
        user = get_object_or_404(Member, email=data.get("email"))
        if user.email_verified:
            raise serializers.ValidationError("email is already verified")
        data["user"] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Serialize fields used for changing a user's password."""

    password = serializers.CharField()
    old_password = serializers.CharField()

    def validate(self, data):
        """Validate the provided user, along with the old and new passwords."""
        user = self.context["request"].user
        password = data.get("password")
        old_password = data.get("old_password")
        if not user.check_password(old_password):
            raise FormattedException(status=HTTP_401_UNAUTHORIZED, m="invalid_password")
        password_validation.validate_password(password, user)
        return data


class GenerateInvitesSerializer(serializers.Serializer):
    """Serialize fields used for generating invite links."""

    amount = serializers.IntegerField(max_value=10000)
    max_uses = serializers.IntegerField(required=False, default=1)
    auto_team = serializers.IntegerField(required=False, default=None)


class InviteCodeSerializer(serializers.ModelSerializer):
    """Serialize fields used for the InviteCode model."""

    class Meta:
        """Specify the model and fields to serialize."""

        model = InviteCode
        fields = ["id", "code", "uses", "max_uses", "auto_team"]


class CreateBotSerializer(serializers.Serializer):
    """Serialize fields used for creating a bot account."""

    username = serializers.CharField()
    is_visible = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()
