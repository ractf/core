from rest_framework.response import Response


class FormattedResponse(Response):

    def __init__(self, d: str = '', m: str = '', s: bool = True, status: int = None, template_name: str = None,
                 headers: list = None, exception: bool = False, content_type: str = None):
        if status and status >= 400:
            s = False
        data = {'s': s, 'm': m, 'd': d}
        super(FormattedResponse, self).__init__(data, status, template_name, headers, exception, content_type)
