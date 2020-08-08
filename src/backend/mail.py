from importlib import import_module
from django.template.loader import render_to_string

from django.conf import settings


if settings.MAIL["SEND"]:  # pragma: no cover
    client = import_module("boto3").client("ses")


def send_email(send_to, subject_line, template_name, **template_details):
    if settings.MAIL["SEND"]:  # pragma: no cover
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

    else:
        print(f"Sending email '{subject_line}' to {send_to} using template {template_name} with details {template_details}")
