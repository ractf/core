import secrets

import pyotp
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from authentication import serializers
from authentication.permissions import HasTwoFactor, VerifyingTwoFactor
from authentication.serializers import RegistrationSerializer, EmailVerificationSerializer, ChangePasswordSerializer
from backend import renderers
from backend.mail import send_email
from backend.response import FormattedResponse
from backend.signals import logout, add_2fa, verify_2fa, password_reset_start, password_reset_start_reject, \
    verify_email, change_password, password_reset
from member.models import TOTPStatus

hide_password = method_decorator(
    sensitive_post_parameters('password', )
)


class LoginView(ObtainAuthToken):
    permission_classes = (~permissions.IsAuthenticated,)
    serializer_class = serializers.LoginSerializer
    throttle_scope = 'login'
    renderer_classes = (renderers.RACTFJSONRenderer,)

    @hide_password
    def dispatch(self, *args, **kwargs):
        return super(LoginView, self).dispatch(*args, **kwargs)


class RegistrationView(CreateAPIView):
    model = get_user_model()
    permission_classes = (~permissions.IsAuthenticated,)
    serializer_class = RegistrationSerializer
    throttle_scope = 'register'

    @hide_password
    def dispatch(self, *args, **kwargs):
        return super(RegistrationView, self).dispatch(*args, **kwargs)


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        logout.send(sender=self.__class__, user=request.user)
        request.user.auth_token.delete()
        return FormattedResponse()


class AddTwoFactorView(APIView):
    permission_classes = (permissions.IsAuthenticated & ~HasTwoFactor,)
    throttle_scope = '2fa'

    def post(self, request):
        totp_secret = pyotp.random_base32()
        request.user.totp_secret = totp_secret
        request.user.totp_status = TOTPStatus.VERIFYING
        request.user.save()
        add_2fa.send(sender=self.__class__, user=request.user)
        return FormattedResponse({'totp_secret': totp_secret})


class VerifyTwoFactorView(APIView):
    permission_classes = (permissions.IsAuthenticated & VerifyingTwoFactor,)
    throttle_scope = '2fa'

    def post(self, request):
        totp = pyotp.TOTP(request.user.totp_secret)
        valid = totp.verify(request.data['otp'], valid_window=1)
        if valid:
            request.user.totp_status = TOTPStatus.ENABLED
            request.user.save()
            verify_2fa.send(sender=self.__class__, user=request.user)
        return FormattedResponse({'valid': valid})


class RequestPasswordResetView(APIView):
    permission_classes = (~permissions.IsAuthenticated,)
    throttle_scope = 'request_password_reset'

    def post(self, request):
        email = request.data['email']
        email_validator = EmailValidator()
        email_validator(email)
        # prevent timing attack - is this necessary?
        try:
            user = get_user_model().objects.get(email=email)
            uid = user.id
            token = user.password_reset_token
            password_reset_start.send(sender=self.__class__, user=user)
        except get_user_model().DoesNotExist:
            password_reset_start_reject.send(sender=self.__class__, email=email)
            uid = -1
            token = ''
            email = 'noreply@ractf.co.uk'
        send_email(email, 'RACTF - Reset Your Password', 'password_reset',
                   url='password_reset?id={}&secret={}'.format(uid, token))
        return FormattedResponse()


class DoPasswordResetView(GenericAPIView):
    permission_classes = (~permissions.IsAuthenticated,)
    serializer_class = serializers.PasswordResetSerializer
    throttle_scope = 'password_reset'

    @hide_password
    def dispatch(self, *args, **kwargs):
        return super(DoPasswordResetView, self).dispatch(*args, **kwargs)

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return FormattedResponse(d=serializer.errors, m='bad_request', status=HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        user = data['user']
        password = data['password']
        user.set_password(password)
        user.password_reset_token = secrets.token_hex()
        user.save()
        password_reset.send(sender=self.__class__, user=user)
        if user.can_login():
            return FormattedResponse({'token': user.issue_token()})
        else:
            return FormattedResponse()


class VerifyEmailView(GenericAPIView):
    permission_classes = (~permissions.IsAuthenticated,)
    throttle_scope = 'verify_email'
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return FormattedResponse(m='invalid_token_or_uid', d=serializer.errors, status=HTTP_400_BAD_REQUEST)
        user = serializer.validated_data['user']
        user.email_verified = True
        user.is_visible = True
        user.save()
        verify_email.send(sender=self.__class__, user=user)
        if user.can_login():
            return FormattedResponse({'token': user.issue_token()})
        else:
            return FormattedResponse()


class ChangePasswordView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = 'change_password'
    serializer_class = ChangePasswordSerializer

    @hide_password
    def dispatch(self, *args, **kwargs):
        return super(ChangePasswordView, self).dispatch(*args, **kwargs)

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        password = serializer.validated_data['password']
        user.set_password(password)
        user.save()
        change_password.send(sender=self.__class__, user=user)
        return FormattedResponse()
