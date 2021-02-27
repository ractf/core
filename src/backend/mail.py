from importlib import import_module
from django.template.loader import render_to_string

from django.conf import settings


if settings.MAIL["SEND"]:  # pragma: no cover
    if settings.MAIL["SEND_MODE"] == "AWS":  # pragma: no cover
        client = import_module("boto3").client("ses")
    elif settings.MAIL["SEND_MODE"] == "SENDGRID":  # pragma: no cover
        import sendgrid
        sg = sendgrid.SendGridAPIClient(settings.MAIL["SENDGRID_API_KEY"])


def send_html(recipients, subject_line, html, txt):
    if not settings.MAIL["SEND"]:
        print(f"Sending html email '{subject_line}' to {', '.join(recipients)}")
        return

    if settings.MAIL["SEND_MODE"] == "AWS":  # pragma: no cover
        for chunk in range(0, len(recipients), 50):
            client.send_email(
                Destination={
                    "BccAddresses": recipients[chunk:chunk + 50]
                },
                Message={
                    "Body": {
                        "Html": {
                            "Charset": "UTF-8",
                            "Data": html
                        },
                        "Text": {
                            "Charset": "UTF-8",
                            "Data": txt
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
        for chunk in range(0, len(recipients), 1000):
            data = {
                "personalizations": [
                    {
                        "bcc": [
                            {"email":v} for v in recipients[chunk:chunk + 1000]
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
                        "value": txt
                    },
                    {
                        "type": "text/html",
                        "value": html
                    }
                ]
            }
            sg.client.mail.send.post(request_body=data)
    elif settings.MAIL["SEND_MODE"] == "SMTP":  # pragma: no cover
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        if settings.MAIL["SMTP_USE_SSL"]:
            smtp = smtplib.SMTP_SSL(settings.MAIL["SEND_SERVER"])
        else:
            smtp = smtplib.SMTP(settings.MAIL["SEND_SERVER"])
        smtp.connect(settings.MAIL["SEND_SERVER"])
        smtp.set_debuglevel(False)
        smtp.login(settings.MAIL["SEND_USERNAME"], settings.MAIL["SEND_PASSWORD"])
        sender = f"{settings.MAIL['SEND_NAME']} <{settings.MAIL['SEND_ADDRESS']}>"

        data = MIMEMultipart('alternative')
        data['To'] = "You <noreply@ractf.co.uk>"
        data['From'] = sender
        data['Subject'] = subject_line

        data.attach(MIMEText(txt, 'plain'))
        data.attach(MIMEText(html, 'html'))

        smtp.sendmail(sender, recipients, data.as_string())


def send_email(send_to, subject_line, template_name, **template_details):
    if not settings.MAIL["SEND"]:
        print(f"Sending email '{subject_line}' to {send_to} using template {template_name} with details {template_details}")

    send_html(
        [send_to],
        subject_line,
        render_to_string(template_name + ".html", template_details),
        render_to_string(template_name + ".txt", template_details)
    )