"""Storages used in RACTF core."""

from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    """S3 storage for challenge files."""

    location = "challenge-files"
    default_acl = None
