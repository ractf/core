from django.shortcuts import render
from django.core import mail


def list(request):
    return render(request, "mail_list.html", context={"emails": getattr(mail, 'outbox', [])})
