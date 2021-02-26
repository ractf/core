from rest_framework.response import Response


class FormattedResponse(Response):

    def __init__(self, d='', m='', s=True, status=None, template_name=None, headers=None, exception=False,
                 content_type=None):
        if status and status >= 400:
            s = False
        data = {'s': s, 'm': m, 'd': d}
        super(FormattedResponse, self).__init__(data, status, template_name, headers, exception, content_type)
