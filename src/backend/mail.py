from django.template.loader import render_to_string
from django.core.mail import send_mail

def send_email(send_to: str, subject_line: str, template_name: str, **template_details) -> None:
    """Wrapper function around `django.core.mail.send_mail` to simplify use of templates."""
    text = render_to_string(template_name + ".txt", template_details)
    html = render_to_string(template_name + ".html", template_details)
    send_mail(subject_line, text, None, [send_to], html_message=html)
