from django.shortcuts import render
from django.core import mail


def list(request):
    try:
        emails = mail.outbox
    except AttributeError:
        emails = []
    return render(request, "mail_list.html", context={"emails": emails})
