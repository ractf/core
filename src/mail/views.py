from django.shortcuts import render


def list(request):
    # This is bad, but Django doesn't create `outbox` until an email is sent
    try:
        from django.core.mail import outbox

        emails = outbox
    except ImportError:
        emails = []
    return render(request, "mail_list.html", context={"emails": emails})
