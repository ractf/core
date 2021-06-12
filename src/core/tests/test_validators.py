"""Tests for validators used in core."""

from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase

from core.validators import printable_name


class PrintableNameValidatorTestCase(APITestCase):
    """Tests for the printable name validator."""

    def test_unprintable_name(self):
        """An unprintable name should be rejected."""
        self.assertRaises(ValidationError, lambda: printable_name(b"\x00".decode("latin-1")))

    def test_printable_name(self):
        """A printable name should be accepted."""
        self.assertIsNone(printable_name("abc"))
