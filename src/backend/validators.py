from string import printable

from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


PRINTABLE_CHARS = set(printable.strip() + " ")


def printable_name(value: str) -> None:
    """Ensure that team names are printable."""
    if not set(value) <= PRINTABLE_CHARS:
        raise ValidationError(
            _("%(value)s contains non-printable characters."),
            params={"value": value},
        )


@deconstructible
class NameValidator(validators.RegexValidator):
    regex = r"^[\w.+ -]+\Z"
    message = _("Enter a valid name. This value may contain only letters, " "numbers, spaces, and ./+/-/_ characters.")
    flags = 0


@deconstructible
class LenientNameValidator(validators.RegexValidator):
    regex = r"^[]+\Z"
    message = _("Enter a valid name. This value may contain only letters, " "numbers, spaces, and ./+/-/_ characters.")
    flags = 0
