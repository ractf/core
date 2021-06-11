"""A package of methods and classes containing logic specific to the challenges app."""

from django.db.models import QuerySet

from challenge import models


def get_file_path(file: "models.File", file_name: str) -> str:
    """Given a file model and the relevant root filename, return the file path."""
    return f"{file.challenge.pk}/{file.md5}/{file_name}"
