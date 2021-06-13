"""Common response formats used in RACTF core."""

from rest_framework.response import Response


class FormattedResponse(Response):
    """A subclass of Response to attempt to make frontend's data format more reasonable to work with."""

    # TODO: Deprecate this.

    def __init__(
        self, d="", m="", s=True, status=None, template_name=None, headers=None, exception=False, content_type=None
    ):
        """Convert the success, data and message attributes to the data object."""
        if status and status >= 400:
            s = False
        data = {"s": s, "m": m, "d": d}
        super(FormattedResponse, self).__init__(data, status, template_name, headers, exception, content_type)
