from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives


def send_email(send_to: str, subject_line: str, template_name: str, **template_details) -> None:
    """Wrapper function around `django.core.mail.send_mail` to simplify use of templates."""
    msg = EmailMultiAlternatives(
        subject_line, render_to_string(template_name + ".txt", template_details), None, [send_to]
    )
    msg.attach_alternative(render_to_string(template_name + ".html", template_details), "text/html")
    msg.send()
