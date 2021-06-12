"""Serializers for the page views."""

from rest_framework import serializers

from pages.models import Page


class PageSerializer(serializers.ModelSerializer):
    """Serializer for pages."""

    class Meta:
        """The fields to serialize."""

        model = Page
        fields = ["id", "url", "title", "content"]
