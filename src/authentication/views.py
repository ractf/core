"""Views and relevant logic for use in authentication."""

import random
import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from django.db import transaction
from django.http import HttpRequest
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView, GenericAPIView, get_object_or_404
from rest_framework.request import Request
from rest_framework.views import APIView

from authentication import serializers
from authentication.mixins import HidePasswordMixin
from authentication.models import BackupCode, InviteCode, PasswordResetToken, TOTPDevice
from authentication.permissions import HasTwoFactor, VerifyingTwoFactor
from core import providers, signals
from core.mail import send_email
from core.permissions import IsBot, IsSudo
from core.response import FormattedResponse
from core.types import AuthenticatedRequest
from core.viewsets import AdminListModelViewSet
from member.models import Member
from team.models import Team


class LoginView(APIView, HidePasswordMixin):
    """View for validating login fields and authenticating users."""

    permission_classes = (~permissions.IsAuthenticated,)
    serializer_class = serializers.LoginSerializer
    throttle_scope = "login"

    def post(self, request: AuthenticatedRequest, *args, **kwargs) -> FormattedResponse:
        """Validate provided login data, and return the relevant login token."""
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if user.has_2fa:
            return FormattedResponse(
                status=status.HTTP_401_UNAUTHORIZED, d={"reason": "2fa_required"}, m="2fa_required"
            )

        token = providers.get_provider("token").issue_token(user)
        return FormattedResponse({"token": token})


class RegistrationView(CreateAPIView, HidePasswordMixin):
    """View for validating and registering new users."""

    model = Member
    permission_classes = (~permissions.IsAuthenticated,)
    serializer_class = serializers.RegistrationSerializer
    throttle_scope = "register"


class LogoutView(APIView):
    """View for deleting user login tokens."""

    permission_classes = (permissions.IsAuthenticated & ~IsBot,)

    def post(self, request: AuthenticatedRequest) -> FormattedResponse:
        """ "Logout the user associated with the provided request."""
        signals.logout.send(sender=LogoutView, user=request.user)
        request.user.tokens.all().delete()
        return FormattedResponse()


class AddTwoFactorView(APIView):
    """View for adding two-factor authentication as a requirement for the user."""

    permission_classes = (permissions.IsAuthenticated & ~HasTwoFactor & ~IsBot,)
    throttle_scope = "2fa"

    def post(self, request: AuthenticatedRequest) -> FormattedResponse:
        """Delete any existing TOTP Devices, provision a new one and return the relevant secret."""
        TOTPDevice.objects.filter(user=request.user).delete()
        totp_device = TOTPDevice.objects.create(user=request.user)
        # TODO: Move this signal to be a post_save on the TOTPDevice model.
        signals.add_2fa.send(sender=AddTwoFactorView, user=request.user)
        return FormattedResponse({"totp_secret": totp_device.totp_secret})


class VerifyTwoFactorView(APIView):
    """View for verifying a user's 2FA code."""

    permission_classes = (permissions.IsAuthenticated & VerifyingTwoFactor & ~IsBot,)
    throttle_scope = "2fa"

    def post(self, request: AuthenticatedRequest) -> FormattedResponse:
        """Validate the provided OTP token and verify the request."""
        otp_token = request.data.get("otp", "")

        if request.user.totp_device is not None and request.user.totp_device.validate_token(otp_token):
            request.user.totp_device.verified = True
            request.user.totp_device.save()
            backup_codes = BackupCode.generate_for(request.user)
            signals.verify_2fa.send(sender=VerifyTwoFactorView, user=request.user)
            return FormattedResponse({"valid": True, "backup_codes": backup_codes})
        return FormattedResponse({"valid": False})


class RemoveTwoFactorView(APIView):
    permission_classes = (permissions.IsAuthenticated & HasTwoFactor & ~IsBot,)
    throttle_scope = "2fa"

    def post(self, request):
        code = request.data["otp"]
        if request.user.totp_device.validate_token(code):
            request.user.totp_device.delete()
            request.user.save()
            signals.remove_2fa.send(sender=RemoveTwoFactorView, user=request.user)
            send_email(request.user.email, "RACTF - 2FA Has Been Disabled", "2fa_removed")
            return FormattedResponse()
        return FormattedResponse(status=status.HTTP_401_UNAUTHORIZED, m="code_incorrect")


class LoginTwoFactorView(APIView, HidePasswordMixin):
    permission_classes = (~permissions.IsAuthenticated,)
    serializer_class = serializers.LoginTwoFactorSerializer
    throttle_scope = "login"

    def issue_token(self, user):
        token = providers.get_provider("token").issue_token(user)
        return FormattedResponse({"token": token})

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if not user.has_2fa:
            return FormattedResponse(
                status=status.HTTP_401_UNAUTHORIZED, d={"reason": "2fa_not_enabled"}, m="2fa_not_enabled"
            )

        token = serializer.data["tfa"]

        if len(token) == 6:
            if user.totp_device is not None and user.totp_device.validate_token(token):
                return self.issue_token(user)
        elif len(token) == 8:
            for code in user.backup_codes.all():
                if token == code.code:
                    code.delete()
                    return self.issue_token(user)

        return FormattedResponse(status=status.HTTP_401_UNAUTHORIZED, d={"reason": "login_failed"}, m="login_failed")


class RegenerateBackupCodesView(APIView):
    permission_classes = (permissions.IsAuthenticated & HasTwoFactor & ~IsBot,)
    serializer_class = serializers.LoginTwoFactorSerializer
    throttle_scope = "2fa"

    def post(self, request, *args, **kwargs):
        backup_codes = BackupCode.generate_for(request.user)
        return FormattedResponse({"backup_codes": backup_codes})


class RequestPasswordResetView(APIView):
    permission_classes = (~permissions.IsAuthenticated,)
    throttle_scope = "request_password_reset"

    def post(self, request):
        email = request.data["email"]
        email_validator = EmailValidator()
        email_validator(email)
        # prevent timing attack - is this necessary?
        try:
            user = Member.objects.get(email=email, email_verified=True)
            token = PasswordResetToken(user=user, token=secrets.token_hex())
            token.save()
            uid = user.pk
            token = token.token
            signals.password_reset_start.send(RequestPasswordResetView, user=user)
        except Member.DoesNotExist:
            signals.password_reset_start_reject.send(RequestPasswordResetView, email=email)
            uid = -1
            token = ""
            email = "noreply@ractf.co.uk"

        if settings.MAIL["SEND"]:
            send_email(
                email,
                "RACTF - Reset Your Password",
                "password_reset",
                url=settings.FRONTEND_URL + "password_reset?id={}&secret={}".format(uid, token),
            )
        return FormattedResponse()


class DoPasswordResetView(GenericAPIView, HidePasswordMixin):
    permission_classes = (~permissions.IsAuthenticated,)
    serializer_class = serializers.PasswordResetSerializer
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return FormattedResponse(d=serializer.errors, m="bad_request", status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        user = data["user"]
        password = data["password"]
        user.set_password(password)
        user.save()

        data["reset_token"].delete()
        signals.password_reset.send(DoPasswordResetView, user=user)
        if user.can_login:
            return FormattedResponse({"token": user.issue_token()})
        else:
            return FormattedResponse()


class VerifyEmailView(GenericAPIView):
    permission_classes = (~permissions.IsAuthenticated,)
    throttle_scope = "verify_email"
    serializer_class = serializers.EmailVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return FormattedResponse(
                m="invalid_token_or_uid",
                d=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.validated_data["user"]
        user.email_verified = True
        user.is_visible = True
        user.save()
        signals.email_verified.send(sender=VerifyEmailView, user=user)
        if user.can_login:
            return FormattedResponse({"token": user.issue_token()})
        else:
            return FormattedResponse()


class ResendEmailView(GenericAPIView):
    permission_classes = (~permissions.IsAuthenticated,)
    throttle_scope = "resend_verify_email"
    serializer_class = serializers.ResendEmailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return FormattedResponse(
                m="invalid_token_or_uid",
                d=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Already verified email is checked in the email serializer.
        user = serializer.validated_data["user"]
        send_email(
            user.email,
            "RACTF - Verify your email",
            "verify",
            url=settings.FRONTEND_URL + "verify?id={}&secret={}".format(user.pk, user.email_token),
        )
        return FormattedResponse("email_resent")


class ChangePasswordView(APIView, HidePasswordMixin):
    permission_classes = (permissions.IsAuthenticated & ~IsBot,)
    throttle_scope = "change_password"
    serializer_class = serializers.ChangePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        password = serializer.validated_data["password"]
        user.set_password(password)
        user.save()
        signals.change_password.send(ChangePasswordView, user=user)
        return FormattedResponse()


class GenerateInvitesView(APIView):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = serializers.GenerateInvitesSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        codes = []
        active_codes = InviteCode.objects.count()
        if serializer.validated_data["auto_team"]:
            team = get_object_or_404(Team, id=serializer.validated_data["auto_team"])
        with transaction.atomic():
            for i in range(active_codes, serializer.validated_data["amount"] + active_codes):
                code = f"{''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])}{hex(i)[2:]}"
                codes.append(code)
                invite = InviteCode(code=code, max_uses=serializer.validated_data["max_uses"])
                if serializer.validated_data["auto_team"]:
                    invite.auto_team = team
                invite.save()
        return FormattedResponse({"invite_codes": codes})


class InviteViewSet(AdminListModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    admin_serializer_class = serializers.InviteCodeSerializer
    list_admin_serializer_class = serializers.InviteCodeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["code", "fully_used", "auto_team"]

    def get_queryset(self):
        return InviteCode.objects.order_by("id")


class CreateBotView(APIView):
    permission_classes = (permissions.IsAdminUser & ~IsBot,)
    serializer_class = serializers.CreateBotSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        bot = Member(
            username=serializer.data["username"],
            email_verified=True,
            is_visible=serializer.data["is_visible"],
            is_staff=serializer.data["is_staff"],
            is_superuser=serializer.data["is_superuser"],
            is_bot=True,
            email=serializer.data["username"] + "@bot.ractf",
        )
        bot.save()
        return FormattedResponse(d={"token": bot.issue_token()}, status=status.HTTP_201_CREATED)


class SudoView(APIView):
    permission_classes = (permissions.IsAdminUser & ~IsBot & ~IsSudo,)

    def post(self, request):
        id = request.data["id"]
        user = get_object_or_404(Member, id=id)
        return FormattedResponse(d={"token": user.issue_token(owner=request.user)})


class DesudoView(APIView):
    permission_classes = (IsSudo,)

    def post(self, request):
        return FormattedResponse(d={"token": request.sudo_from.issue_token()})
