from django.core import validators
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class NameValidator(validators.RegexValidator):
    regex = r'^[\w.+ -]+\Z'
    message = _(
        'Enter a valid name. This value may contain only letters, '
        'numbers, spaces, and ./+/-/_ characters.'
    )
    flags = 0


@deconstructible
class LenientNameValidator(validators.RegexValidator):
    regex = r'^[]+\Z'
    message = _(
        'Enter a valid name. This value may contain only letters, '
        'numbers, spaces, and ./+/-/_ characters.'
    )
    flags = 0
