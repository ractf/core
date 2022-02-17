from rest_framework.renderers import JSONRenderer


class RACTFJSONRenderer(JSONRenderer):
    media_type = "application/json"
    format = "json"
    charset = "utf-8"
    render_style = "text"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None or not isinstance(data, dict) or "s" not in data:
            response = {"s": True, "d": data, "m": ""}
        else:
            response = data
        return super(RACTFJSONRenderer, self).render(response, accepted_media_type, renderer_context)
