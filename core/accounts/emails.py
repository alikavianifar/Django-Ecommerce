"""Email sending utilities for account verification."""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from accounts.tokens import make_verification_token


def send_verification_email(request, user) -> None:
    """Send an HTML verification email with a signed token link."""
    token = make_verification_token(user)

    verify_url = request.build_absolute_uri(
        f"/accounts/verify-email/{token}/"
    )

    context = {
        "user": user,
        "verify_url": verify_url,
        "expiry_hours": getattr(settings, "VERIFICATION_TOKEN_MAX_AGE", 86400) // 3600,
    }

    html_content = render_to_string("accounts/emails/verify_email.html", context)
    plain_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject="Verify your email address",
        body=plain_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)