from rest_framework import serializers

from hint.models import Hint, HintUse


def is_used(context, instance):
    return context['request'].user.team is not None and context['request'].user.team.hints_used.filter(
        hint=instance).exists()


class HintUseSerializer(serializers.ModelSerializer):
    class Meta:
        model = HintUse
        fields = ['id', 'hint', 'team', 'user', 'timestamp']


class HintSerializer(serializers.ModelSerializer):
    text = serializers.SerializerMethodField()
    used = serializers.SerializerMethodField()

    class Meta:
        model = Hint
        fields = ['id', 'name', 'penalty', 'challenge', 'text', 'used']

    def get_text(self, instance):
        if (self.context['request'].user.is_staff and not self.context['request'].user.should_deny_admin()) or instance.used:
            return instance.text
        else:
            return ''

    def get_used(self, instance):
        return instance.used


class CreateHintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hint
        fields = ['id', 'name', 'penalty', 'challenge', 'text']
        read_only_fields = ['id']


class FullHintSerializer(serializers.ModelSerializer):
    used = serializers.SerializerMethodField()

    class Meta:
        model = Hint
        fields = ['id', 'name', 'penalty', 'challenge', 'text', 'used']

    def get_used(self, instance):
        return is_used(self.context, instance)


class UseHintSerializer(serializers.Serializer):
    id = serializers.IntegerField()
