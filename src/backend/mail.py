from importlib import import_module
from django.template.loader import render_to_string

from django.conf import settings


if settings.MAIL["SEND"]:  # pragma: no cover
    if settings.MAIL["SEND_MODE"] == "AWS":  # pragma: no cover
        client = import_module("boto3").client("ses")
    elif settings.MAIL["SEND_MODE"] == "SENDGRID":  # pragma: no cover
        import sendgrid
        sg = sendgrid.SendGridAPIClient(settings.MAIL["EMAIL_USER"])
    elif settings.MAIL["SEND_MODE"] == "SMTP":
        from smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        smtp = smtplib.SMTP_SSL(settings.MAIL["EMAIL_SERVER"])
        smtp.set_debuglevel(False)
        smtp.login(settings.MAIL["EMAIL_USER"], settings.MAIL["EMAIL_PASS"])


def send_email(send_to, subject_line, template_name, **template_details):
    if settings.MAIL["SEND"]:  # pragma: no cover
        if settings.MAIL["SEND_MODE"] == "AWS":  # pragma: no cover
            template_details["url"] = settings.FRONTEND_URL + template_details["url"]
            client.send_email(
                Destination={
                    "ToAddresses": [
                        send_to
                    ]
                },
                Message={
                    "Body": {
                        "Html": {
                            "Charset": "UTF-8",
                            "Data": render_to_string(template_name + ".html", template_details)
                        },
                        "Text": {
                            "Charset": "UTF-8",
                            "Data": render_to_string(template_name + ".txt", template_details)
                        }
                    },
                    "Subject": {
                        "Charset": "UTF-8",
                        "Data": subject_line
                    }
                },
                Source=f"{settings.MAIL['SEND_NAME']} <{settings.MAIL['SEND_ADDRESS']}>"
            )
        elif settings.MAIL["SEND_MODE"] == "SENDGRID":  # pragma: no cover
            data = {
                "personalizations": [
                    {
                        "to": [
                            {
                                "email": send_to
                            }
                        ],
                        "subject": subject_line
                    }
                ],
                "from": {
                    "email": settings.MAIL['SEND_ADDRESS'],
                    "name": settings.MAIL['SEND_NAME']
                },
                "content": [
                    {
                        "type": "text/plain",
                        "value": render_to_string(template_name + ".txt", template_details)
                    },
                    {
                        "type": "text/html",
                        "value": render_to_string(template_name + ".html", template_details)
                    }
                ]
            }
            sg.client.mail.send.post(request_body=data)
        elif settings.MAIL["SEND_MODE"] == "SMTP":  # pragma: no cover
            sender = f"{settings.MAIL['SEND_NAME']} <{settings.MAIL['SEND_ADDRESS']}>"

            data = MIMEMultipart('alternative')
            data['To'] = send_to
            data['From'] = sender
            data['Subject'] = subject_line

            msg.attach(MIMEText(render_to_string(template_name + ".txt", template_details), 'plain'))
            msg.attach(MIMEText(render_to_string(template_name + ".html", template_details), 'html'))

            smtp.sendmail(sender, send_to, data.as_string())
    else:
        print(f"Sending email '{subject_line}' to {send_to} using template {template_name} with details {template_details}")
