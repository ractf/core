from django.template import Library, loader

register = Library()


@register.filter(name='center', is_safe=True, needs_autoescape=False)
def center(value, arg=""):
    template = loader.get_template("components/center.html")
    return template.render({"value": value, "pad": arg})
