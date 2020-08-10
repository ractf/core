from django.contrib.auth import get_user_model, password_validation
from django.utils import timezone
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.status import HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED

from authentication.models import InviteCode, PasswordResetToken
from backend.exceptions import FormattedException
from plugins import providers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)

    def validate(self, data):
        user = providers.get_provider('login').login_user(**data, context=self.context)
        data['user'] = user
        return data


class LoginTwoFactorSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)
    tfa = serializers.CharField(max_length=255, allow_null=True, allow_blank=True)

    def validate(self, data):
        user = providers.get_provider('login').login_user(**data, context=self.context)
        data['user'] = user
        return data


class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)
    email = serializers.EmailField()
    invite = serializers.CharField(max_length=64, required=False, default=None)

    def create(self, validated_data):
        return providers.get_provider('registration').register_user(**validated_data, context=self.context)

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
        user = get_object_or_404(get_user_model(), id=uid)
        reset_token = get_object_or_404(PasswordResetToken, token=token, user_id=uid, expires__lt=timezone.now())
        password_validation.validate_password(password, reset_token)
        data['user'] = user
        data['reset_token'] = reset_token
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


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        user = get_object_or_404(get_user_model(), email=data.get('email'))
        if user.email_verified:
            raise FormattedException(m='email_already_verified', status_code=HTTP_403_FORBIDDEN)
        data['user'] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField()

    def validate(self, data):
        user = self.context['request'].user
        password = data.get('password')
        old_password = data.get('old_password')
        if not user.check_password(old_password):
            raise FormattedException(status_code=HTTP_401_UNAUTHORIZED, m='invalid_password')
        password_validation.validate_password(password, user)
        return data


class GenerateInvitesSerializer(serializers.Serializer):
    amount = serializers.IntegerField(max_value=10000)
    max_uses = serializers.IntegerField(required=False, default=1)
    auto_team = serializers.IntegerField(required=False, default=None)


class InviteCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteCode
        fields = ['id', 'code', 'uses', 'max_uses', 'auto_team']
