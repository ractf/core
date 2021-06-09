from django.conf import settings
from django.shortcuts import render
from django.views.generic import TemplateView


class CatchAllView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(template_name="404.html", context={"link": settings.FRONTEND_URL}, request=request, status=404)
