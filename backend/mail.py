import requests_unixsocket

from backend import settings


def send_email(send_to, subject_line, template_name, **template_details):
    if settings.SEND_MAIL:  # pragma: no cover
        session = requests_unixsocket.Session()
        if 'url' in template_details:
            template_details['url'] = settings.FRONTEND_URL + template_details['url']
        session.post(settings.MAIL_SOCK_URL, data={"to": send_to, "subject": subject_line,
                                                   "template": template_name, **template_details})
    else:
        print(f"Sending email '{subject_line}' to {send_to} using template {template_name} with details {template_details}")
