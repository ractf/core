"""Views and relevant logic for use in authentication."""

import random
import secrets
import string

from django.conf import settings
from django.core.validators import EmailValidator
from django.db import transaction
from django.db.models import QuerySet
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

INVITE_CHARACTERS = string.ascii_letters + string.digits


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

        if user.enabled_2fa:
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
        """Logout the user associated with the provided request."""
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
    """View for removing 2FA from a user's account."""

    permission_classes = (permissions.IsAuthenticated & HasTwoFactor & ~IsBot,)
    throttle_scope = "2fa"

    def post(self, request: AuthenticatedRequest) -> FormattedResponse:
        """Remove the user's TOTP device and send them an email."""
        otp_token = request.data.get("otp", "")

        if request.user.totp_device.validate_token(otp_token):
            request.user.totp_device.delete()
            request.user.save()
            # TODO: Move this signal to be a post_delete on the TOTPDevice model.
            signals.remove_2fa.send(sender=RemoveTwoFactorView, user=request.user)
            send_email(request.user.email, "RACTF - 2FA Has Been Disabled", "2fa_removed")
            return FormattedResponse()
        return FormattedResponse(status=status.HTTP_401_UNAUTHORIZED, m="code_incorrect")


class LoginTwoFactorView(APIView, HidePasswordMixin):
    """View for logging in a user with 2FA enabled."""

    permission_classes = (~permissions.IsAuthenticated,)
    serializer_class = serializers.LoginTwoFactorSerializer
    throttle_scope = "login"

    def post(self, request: Request, *args, **kwargs) -> FormattedResponse:
        """Log in a user using their provided two factor auth token."""
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        provider = providers.get_provider("token")

        if not user.enabled_2fa:
            return FormattedResponse(
                status=status.HTTP_401_UNAUTHORIZED, d={"reason": "2fa_not_enabled"}, m="2fa_not_enabled"
            )

        token = serializer.data["tfa"]

        if len(token) == 6:
            if user.totp_device is not None and user.totp_device.validate_token(token):
                return FormattedResponse({"token": provider.issue_token(user)})

        elif len(token) == 8:
            for code in user.backup_codes.filter(code=token):
                code.delete()
                return FormattedResponse({"token": provider.issue_token(user)})

        return FormattedResponse(status=status.HTTP_401_UNAUTHORIZED, d={"reason": "login_failed"}, m="login_failed")


class RegenerateBackupCodesView(APIView):
    """View for re-generating a user's backup codes."""

    permission_classes = (permissions.IsAuthenticated & HasTwoFactor & ~IsBot,)
    serializer_class = serializers.LoginTwoFactorSerializer
    throttle_scope = "2fa"

    def post(self, request: AuthenticatedRequest, *args, **kwargs) -> FormattedResponse:
        """Regenerate the user's backup codes, and return the new set."""
        BackupCode.objects.filter(user=request.user).delete()
        backup_codes = BackupCode.generate_for(request.user)
        return FormattedResponse({"backup_codes": backup_codes})


class RequestPasswordResetView(APIView):
    """View for requesting a password reset on the user's account."""

    permission_classes = (~permissions.IsAuthenticated,)
    throttle_scope = "request_password_reset"

    def post(self, request: AuthenticatedRequest) -> FormattedResponse:
        """Given an email, trigger a password reset request on the relevant user."""
        email = request.data.get("email", "")
        email_validator = EmailValidator()
        email_validator(email)

        # The following logic may be needed to prevent a timing attack.
        # TODO: Evaluate whether this is necessary.
        try:
            user = Member.objects.get(email=email, email_verified=True)
            token = PasswordResetToken.objects.create(user=user, token=secrets.token_hex())
            signals.password_reset_start.send(RequestPasswordResetView, user=user)
            user_id, token = user.pk, token.token

        except Member.DoesNotExist:
            signals.password_reset_start_reject.send(RequestPasswordResetView, email=email)
            user_id, token, email = -1, "", "noreply@ractf.co.uk"

        if settings.MAIL["SEND"]:
            send_email(
                email,
                "RACTF - Reset Your Password",
                "password_reset",
                url=settings.FRONTEND_URL + f"password_reset?id={user_id}&secret={token}",
            )
        return FormattedResponse()


class DoPasswordResetView(GenericAPIView, HidePasswordMixin):
    """View for fulfilling a user's password reset request."""

    permission_classes = (~permissions.IsAuthenticated,)
    serializer_class = serializers.PasswordResetSerializer
    throttle_scope = "password_reset"

    def post(self, request: AuthenticatedRequest) -> FormattedResponse:
        """Validate the provided token and password, and issue a new one."""
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return FormattedResponse(d=serializer.errors, m="bad_request", status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user, password = data["user"], data["password"]
        user.set_password(password)
        user.save()

        data["reset_token"].delete()
        signals.password_reset.send(DoPasswordResetView, user=user)
        if user.can_login:
            return FormattedResponse({"token": user.issue_token()})
        return FormattedResponse()


class VerifyEmailView(GenericAPIView):
    """View for verifying the provided user's email address."""

    permission_classes = (~permissions.IsAuthenticated,)
    throttle_scope = "verify_email"
    serializer_class = serializers.EmailVerificationSerializer

    def post(self, request: AuthenticatedRequest) -> FormattedResponse:
        """Verify the user and verification token, then verify the user."""
        # TODO: Use Django forms in these situations to reduce repeated logic.
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
    """View for resending the user's verification email."""

    permission_classes = (~permissions.IsAuthenticated,)
    throttle_scope = "resend_verify_email"
    serializer_class = serializers.ResendEmailSerializer

    def post(self, request: AuthenticatedRequest) -> FormattedResponse:
        """Validate the provided email, and send the relevant verification email."""
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
            url=settings.FRONTEND_URL + f"verify?id={user.pk}&secret={user.email_token}",
        )
        return FormattedResponse("email_resent")


class ChangePasswordView(APIView, HidePasswordMixin):
    """View for changing the provided user's password."""

    permission_classes = (permissions.IsAuthenticated & ~IsBot,)
    throttle_scope = "change_password"
    serializer_class = serializers.ChangePasswordSerializer

    def post(self, request: AuthenticatedRequest) -> FormattedResponse:
        """Validate the provided password, and send the password changed signal."""
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user, password = request.user, serializer.validated_data["password"]
        user.set_password(password)
        user.save()
        signals.change_password.send(ChangePasswordView, user=user)
        return FormattedResponse()


class GenerateInvitesView(APIView):
    """View used by admins to generate invites."""

    permission_classes = (permissions.IsAdminUser,)
    serializer_class = serializers.GenerateInvitesSerializer

    def post(self, request: AuthenticatedRequest) -> FormattedResponse:
        """Generate a set of new invite codes, and return them to the user."""
        invite_codes, team = [], None

        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        active_codes = InviteCode.objects.count()

        auto_team, amount, max_uses = (serializer.validated_data[key] for key in ("auto_team", "amount", "max_uses"))

        if serializer.validated_data["auto_team"]:
            team = get_object_or_404(Team, pk=auto_team)

        with transaction.atomic():
            for current_code in range(active_codes, amount + active_codes):
                code = "".join(random.choice(INVITE_CHARACTERS) for _ in range(8))
                code += hex(current_code)[2:]
                invite_codes.append(code)
                invite = InviteCode(code=code, max_uses=max_uses)
                if auto_team:
                    invite.auto_team = team
                invite.save()
        return FormattedResponse({"invite_codes": invite_codes})


class InviteViewSet(AdminListModelViewSet):
    """A viewset for querying on all invite codes in the database."""

    permission_classes = (permissions.IsAdminUser,)
    admin_serializer_class = serializers.InviteCodeSerializer
    list_admin_serializer_class = serializers.InviteCodeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["code", "fully_used", "auto_team"]

    def get_queryset(self) -> "QuerySet[InviteCode]":
        """Return all InviteCodes, ordered by ID."""
        return InviteCode.objects.order_by("id")


class CreateBotView(APIView):
    """View for admins to create a new bot user."""

    permission_classes = (permissions.IsAdminUser & ~IsBot,)
    serializer_class = serializers.CreateBotSerializer

    def post(self, request: AuthenticatedRequest) -> FormattedResponse:
        """Create a new member with the 'is_bot' attribute, then return the bot token."""
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        bot = Member.objects.create(
            username=serializer.data["username"],
            email_verified=True,
            is_visible=serializer.data["is_visible"],
            is_staff=serializer.data["is_staff"],
            is_superuser=serializer.data["is_superuser"],
            is_bot=True,
            email=serializer.data["username"] + "@bot.ractf",
        )
        return FormattedResponse(d={"token": bot.issue_token()}, status=status.HTTP_201_CREATED)


class SudoView(APIView):
    """View for bots to authenticate as a normal user."""

    permission_classes = (permissions.IsAdminUser & ~IsBot & ~IsSudo,)

    def post(self, request: Request) -> FormattedResponse:
        """Get the associated Member object, and issue a new token for them."""
        user = get_object_or_404(Member, pk=request.data["id"])
        return FormattedResponse(d={"token": user.issue_token(owner=request.user)})


class DesudoView(APIView):
    """View to return a bot user to their original state."""

    permission_classes = (IsSudo,)

    def post(self, request: Request) -> FormattedResponse:
        """Issue a new normal token for this user, and return it."""
        return FormattedResponse(d={"token": request.sudo_from.issue_token()})
