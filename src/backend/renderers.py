from rest_framework.renderers import JSONRenderer


class RACTFJSONRenderer(JSONRenderer):
    media_type = "application/json"
    format = "json"
    charset = "utf-8"
    render_style = "text"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if (
            renderer_context
            and renderer_context.get("request")
            and "X-Reasonable" in renderer_context.get("request").headers
        ):
            if renderer_context.get("response").status_code >= 400:
                return super(RACTFJSONRenderer, self).render(data, accepted_media_type, renderer_context)

            if data is None or not isinstance(data, dict) or "s" not in data:
                return super(RACTFJSONRenderer, self).render(data, accepted_media_type, renderer_context)
            if data["m"] and data["d"]:
                return super(RACTFJSONRenderer, self).render(data, accepted_media_type, renderer_context)
            elif data["m"]:
                return super(RACTFJSONRenderer, self).render(
                    {"message": data["m"]}, accepted_media_type, renderer_context
                )
            elif data["d"]:
                return super(RACTFJSONRenderer, self).render(data["d"], accepted_media_type, renderer_context)

        if data is None or not isinstance(data, dict) or "s" not in data:
            response = {"s": True, "d": data, "m": ""}
        else:
            response = data
        return super(RACTFJSONRenderer, self).render(response, accepted_media_type, renderer_context)
