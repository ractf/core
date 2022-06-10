import random
import secrets
import string

from django.conf import settings
from django.core.validators import EmailValidator
from django.db import IntegrityError, transaction
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework.generics import CreateAPIView, GenericAPIView, get_object_or_404
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)
from rest_framework.views import APIView

from authentication import serializers
from authentication.models import BackupCode, InviteCode, PasswordResetToken, TOTPDevice
from authentication.permissions import HasTwoFactor, VerifyingTwoFactor
from authentication.serializers import (
    ChangePasswordSerializer,
    CreateBotSerializer,
    EmailSerializer,
    EmailVerificationSerializer,
    GenerateInvitesSerializer,
    InviteCodeSerializer,
    RegistrationSerializer,
)
from backend.mail import send_email
from backend.permissions import IsBot, IsSudo
from backend.response import FormattedResponse
from backend.signals import (
    add_2fa,
    change_password,
    email_verified,
    logout,
    password_reset,
    password_reset_start,
    password_reset_start_reject,
    remove_2fa,
    verify_2fa,
)
from backend.viewsets import AdminListModelViewSet
from config import config
from member.models import Member
from plugins import providers
from team.models import Team

hide_password = method_decorator(
    sensitive_post_parameters(
        "password",
    )
)


class LoginView(APIView):
    permission_classes = (~permissions.IsAuthenticated,)
    serializer_class = serializers.LoginSerializer
    throttle_scope = "login"

    @hide_password
    def dispatch(self, *args, **kwargs):
        return super(LoginView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if user.has_2fa():
            return FormattedResponse(status=HTTP_401_UNAUTHORIZED, d={"reason": "2fa_required"}, m="2fa_required")

        token = providers.get_provider("token").issue_token(user)
        return FormattedResponse({"token": token})


class RegistrationView(CreateAPIView):
    model = Member
    permission_classes = (~permissions.IsAuthenticated,)
    serializer_class = RegistrationSerializer
    throttle_scope = "register"

    @hide_password
    def dispatch(self, *args, **kwargs):
        return super(RegistrationView, self).dispatch(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            # If we need granularity to see whether email or username is in used here,
            # check the constraint name that is returned.
            return FormattedResponse(m="email_or_username_in_use", status=HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated & ~IsBot,)

    def post(self, request):
        logout.send(sender=self.__class__, user=request.user)
        request.user.tokens.all().delete()
        return FormattedResponse()


class AddTwoFactorView(APIView):
    permission_classes = (permissions.IsAuthenticated & ~HasTwoFactor & ~IsBot,)
    throttle_scope = "2fa"

    def post(self, request):
        if TOTPDevice.objects.filter(user=request.user).exists():
            TOTPDevice.objects.get(user=request.user).delete()
        totp_device = TOTPDevice(user=request.user)
        totp_device.save()
        add_2fa.send(sender=self.__class__, user=request.user)
        return FormattedResponse({"totp_secret": totp_device.totp_secret})


class VerifyTwoFactorView(APIView):
    permission_classes = (permissions.IsAuthenticated & VerifyingTwoFactor & ~IsBot,)
    throttle_scope = "2fa"

    def post(self, request):
        if request.user.totp_device is not None and request.user.totp_device.validate_token(request.data["otp"]):
            request.user.totp_device.verified = True
            request.user.totp_device.save()
            backup_codes = BackupCode.generate(request.user)
            verify_2fa.send(sender=self.__class__, user=request.user)
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
            remove_2fa.send(sender=self.__class__, user=request.user)
            send_email(request.user.email, f"{config.get('event_name')} - 2FA Has Been Disabled", "2fa_removed")
            return FormattedResponse()
        return FormattedResponse(status=HTTP_401_UNAUTHORIZED, m="code_incorrect")


class LoginTwoFactorView(APIView):
    permission_classes = (~permissions.IsAuthenticated,)
    serializer_class = serializers.LoginTwoFactorSerializer
    throttle_scope = "login"

    @hide_password
    def dispatch(self, *args, **kwargs):
        return super(LoginTwoFactorView, self).dispatch(*args, **kwargs)

    def issue_token(self, user):
        token = providers.get_provider("token").issue_token(user)
        return FormattedResponse({"token": token})

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if not user.has_2fa():
            return FormattedResponse(status=HTTP_401_UNAUTHORIZED, d={"reason": "2fa_not_enabled"}, m="2fa_not_enabled")

        token = serializer.data["tfa"]

        if len(token) == 6:
            if user.totp_device is not None and user.totp_device.validate_token(token):
                return self.issue_token(user)
        elif len(token) == 8:
            for code in user.backup_codes.all():
                if token == code.code:
                    code.delete()
                    return self.issue_token(user)

        return FormattedResponse(status=HTTP_401_UNAUTHORIZED, d={"reason": "login_failed"}, m="login_failed")


class RegenerateBackupCodesView(APIView):
    permission_classes = (permissions.IsAuthenticated & HasTwoFactor & ~IsBot,)
    serializer_class = serializers.LoginTwoFactorSerializer
    throttle_scope = "2fa"

    def post(self, request, *args, **kwargs):
        backup_codes = BackupCode.generate(request.user)
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
            password_reset_start.send(sender=self.__class__, user=user)
        except Member.DoesNotExist:
            password_reset_start_reject.send(sender=self.__class__, email=email)
            uid = -1
            token = ""
            email = "noreply@ractf.co.uk"

        if settings.EMAIL_ENABLED:
            send_email(
                email,
                f"{config.get('event_name')} - Reset Your Password",
                "password_reset",
                url=settings.FRONTEND_URL + "password_reset?id={}&secret={}".format(uid, token),
            )
        return FormattedResponse()


class DoPasswordResetView(GenericAPIView):
    permission_classes = (~permissions.IsAuthenticated,)
    serializer_class = serializers.PasswordResetSerializer
    throttle_scope = "password_reset"

    @hide_password
    def dispatch(self, *args, **kwargs):
        return super(DoPasswordResetView, self).dispatch(*args, **kwargs)

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return FormattedResponse(d=serializer.errors, m="bad_request", status=HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        user = data["user"]
        password = data["password"]
        user.set_password(password)
        user.save()

        data["reset_token"].delete()
        password_reset.send(sender=self.__class__, user=user)
        if user.can_login():
            return FormattedResponse({"token": user.issue_token()})
        else:
            return FormattedResponse()


class VerifyEmailView(GenericAPIView):
    permission_classes = (~permissions.IsAuthenticated,)
    throttle_scope = "verify_email"
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return FormattedResponse(
                m="invalid_token_or_uid",
                d=serializer.errors,
                status=HTTP_400_BAD_REQUEST,
            )
        user = serializer.validated_data["user"]
        user.email_verified = True
        user.is_visible = True
        user.save()
        email_verified.send(sender=self.__class__, user=user)
        if user.can_login():
            return FormattedResponse({"token": user.issue_token()})
        else:
            return FormattedResponse()


class ResendEmailView(GenericAPIView):
    permission_classes = (~permissions.IsAuthenticated,)
    throttle_scope = "resend_verify_email"
    serializer_class = EmailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return FormattedResponse(
                m="invalid_token_or_uid",
                d=serializer.errors,
                status=HTTP_400_BAD_REQUEST,
            )

        # Already verified email is checked in the email serializer.
        user = serializer.validated_data["user"]
        send_email(
            user.email,
            f"{config.get('event_name')} - Verify your email",
            "verify",
            url=settings.FRONTEND_URL + "verify?id={}&secret={}".format(user.pk, user.email_token),
        )
        return FormattedResponse("email_resent")


class ChangePasswordView(APIView):
    permission_classes = (permissions.IsAuthenticated & ~IsBot,)
    throttle_scope = "change_password"
    serializer_class = ChangePasswordSerializer

    @hide_password
    def dispatch(self, *args, **kwargs):
        return super(ChangePasswordView, self).dispatch(*args, **kwargs)

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        password = serializer.validated_data["password"]
        user.set_password(password)
        user.save()
        change_password.send(sender=self.__class__, user=user)
        return FormattedResponse()


class GenerateInvitesView(APIView):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = GenerateInvitesSerializer

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
    admin_serializer_class = InviteCodeSerializer
    list_admin_serializer_class = InviteCodeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["code", "fully_used", "auto_team"]

    def get_queryset(self):
        return InviteCode.objects.order_by("id")


class CreateBotView(APIView):
    permission_classes = (permissions.IsAdminUser & ~IsBot,)
    serializer_class = CreateBotSerializer

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

        try:
            bot.save()
        except IntegrityError:
            return FormattedResponse(m="username_already_exists", status=HTTP_400_BAD_REQUEST)
        return FormattedResponse(d={"token": bot.issue_token()}, status=HTTP_201_CREATED)


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
