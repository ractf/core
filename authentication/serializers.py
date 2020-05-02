import re
import time

import pyotp as pyotp
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.status import HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED, HTTP_400_BAD_REQUEST

from backend.exceptions import FormattedException
from backend.mail import send_email
from backend.signals import login_reject, login, register_reject, register
from config import config
from member.models import TOTPStatus


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(label=_("Username"))
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False
    )
    otp = serializers.CharField(max_length=6, label=_("OTP"), allow_null=True, allow_blank=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        otp = data.get('otp')
        user = authenticate(request=self.context.get('request'),
                            username=username, password=password)
        if not user:
            login_reject.send(sender=self.__class__, username=username, reason='creds')
            raise FormattedException(m='incorrect_username_or_password', d={'reason': 'incorrect_username_or_password'},
                                     status_code=HTTP_401_UNAUTHORIZED)

        if not user.email_verified and not user.is_superuser:
            login_reject.send(sender=self.__class__, username=username, reason='email')
            raise FormattedException(m='email_verification_required', d={'reason': 'email_verification_required'},
                                     status_code=HTTP_401_UNAUTHORIZED)

        if not user.can_login():
            login_reject.send(sender=self.__class__, username=username, reason='closed')
            raise FormattedException(m='login_not_open', d={'reason': 'login_not_open'},
                                     status_code=HTTP_401_UNAUTHORIZED)

        if user.totp_status == TOTPStatus.ENABLED:
            if not otp or otp == '':
                login_reject.send(sender=self.__class__, username=username, reason='no_2fa')
                raise FormattedException(m='2fa_required', d={'reason': '2fa_required'},
                                         status_code=HTTP_401_UNAUTHORIZED)
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(otp, valid_window=1):
                login_reject.send(sender=self.__class__, username=username, reason='incorrect_2fa')
                raise FormattedException(m='incorrect_2fa', d={'reason': 'incorrect_2fa'},
                                         status_code=HTTP_401_UNAUTHORIZED)
        login.send(sender=self.__class__, user=user)
        data['user'] = user
        return data


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'password', 'email',)
        write_only_fields = ('password',)
        read_only_fields = ('id',)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        if config.get('email_regex') and not re.compile(config.get('email_regex')).match(email) or \
                not email.endswith(config.get('email_domain')):
            raise FormattedException(m='invalid_email', status_code=HTTP_400_BAD_REQUEST)
        register_end_time = config.get('register_end_time')
        if not (config.get('enable_registration') and time.time() >= config.get('register_start_time')) \
                and (register_end_time < 0 or register_end_time > time.time()):
            register_reject.send(sender=self.__class__, username=username, email=email)
            raise FormattedException(m='registration_not_open', status_code=HTTP_403_FORBIDDEN)
        user = get_user_model()(
            username=username,
            email=email
        )
        if not get_user_model().objects.all().exists():
            user.is_staff = True
        password_validation.validate_password(password, user)
        data['user'] = user
        return data

    def create(self, validated_data):
        user = validated_data['user']
        user.set_password(validated_data['password'])
        user.save()
        token = user.email_token
        send_email(user.email, 'RACTF - Verify your email', 'verify',
                   url='verify?id={}&secret={}'.format(user.id, token))
        register.send(sender=self.__class__, user=user)
        return user

    def to_representation(self, instance):
        representation = super(RegistrationSerializer, self).to_representation(instance)
        representation.pop('password')
        return representation


class PasswordResetSerializer(serializers.Serializer):
    uid = serializers.IntegerField()
    token = serializers.CharField(max_length=64)
    password = serializers.CharField()

    def validate(self, data):
        uid = data.get('uid')
        token = data.get('token')
        password = data.get('password')
        user = get_object_or_404(get_user_model(), id=uid, password_reset_token=token)
        password_validation.validate_password(password, user)
        data['user'] = user
        return data


class EmailVerificationSerializer(serializers.Serializer):
    uid = serializers.IntegerField()
    token = serializers.CharField(max_length=64)

    def validate(self, data):
        uid = int(data.get('uid'))
        token = data.get('token')
        user = get_object_or_404(get_user_model(), id=uid, email_token=token)
        if user.email_verified:
            raise FormattedException(m='email_already_verified', status_code=HTTP_403_FORBIDDEN)
        data['user'] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField()

    def validate(self, data):
        user = self.context['request'].user
        password = data.get('password')
        password_validation.validate_password(password, user)
        return data
