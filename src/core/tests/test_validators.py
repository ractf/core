from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase

from core.validators import printable_name


class PrintableNameValidatorTestCase(APITestCase):
    def test_unprintable_name(self):
        self.assertRaises(ValidationError, lambda: printable_name(b"\x00".decode("latin-1")))

    def test_printable_name(self):
        self.assertIsNone(printable_name("abc"))
