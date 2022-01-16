from os import path

from anymail.message import attach_inline_image_file
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_email(send_to: str, subject_line: str, template_name: str, **template_details) -> None:
    """Wrapper function around `django.core.mail.send_mail` to simplify use of templates."""
    msg = EmailMultiAlternatives(
        subject_line, render_to_string(template_name + ".txt", template_details), None, [send_to]
    )
    cid = attach_inline_image_file(msg, path.join(settings.BASE_DIR, "logo.png"))
    template_details |= {"logo": cid}
    msg.attach_alternative(render_to_string(template_name + ".html", template_details), "text/html")
    msg.send()
