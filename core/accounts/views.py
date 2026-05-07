"""Authentication views: login, logout, registration, and email verification.

Includes rate limiting on login, registration, and email resend endpoints
to prevent brute-force and abuse.
"""

import logging

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView, View
from django_ratelimit.decorators import ratelimit

from accounts.emails import send_verification_email
from accounts.forms import AuthenticationForm, RegisterForm
from accounts.models.users import User, UserType
from accounts.tokens import verify_verification_token

logger = logging.getLogger(__name__)


class LoginView(auth_views.LoginView):
    """Email-based login with session cycling and rate limiting."""

    template_name = "accounts/login.html"
    form_class = AuthenticationForm
    redirect_authenticated_user = True

    @method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session.cycle_key()
        logger.info("User %s logged in successfully", self.request.user.email)
        return response

    def get_success_url(self):
        redirect_url = self.get_redirect_url()
        if redirect_url:
            return redirect_url
        user = self.request.user
        if getattr(user, "type", None) in (
            UserType.admin.value,
            UserType.superuser.value,
        ):
            return reverse_lazy("dashboard:admin:home")
        return "/"


class LogoutView(auth_views.LogoutView):
    """Standard logout view."""

    pass


class RegisterView(FormView):
    """User registration with email verification and rate limiting."""

    template_name = "accounts/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("accounts:verify-email-sent")

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("/")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        logger.info("New user registered: %s", user.email)

        try:
            send_verification_email(self.request, user)
        except Exception:
            logger.exception("Verification email failed for user %s", user.pk)

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class VerifyEmailSentView(View):
    """Confirmation page shown after registration (check your inbox)."""

    def get(self, request):
        return render(request, "accounts/verify_email_sent.html")


class VerifyEmailConfirmView(View):
    """Verify a user's email address using a signed token."""

    def get(self, request, token: str):
        user_id = verify_verification_token(token)

        if user_id is None:
            messages.error(
                request,
                "This verification link is invalid or has expired. "
                "Please request a new one.",
            )
            return redirect("accounts:verify-email-resend")

        user = get_object_or_404(User, pk=user_id)

        if user.is_verified:
            messages.info(request, "Your email is already verified. You can log in.")
            return redirect("accounts:login")

        user.is_verified = True
        user.save(update_fields=["is_verified"])
        logger.info("Email verified for user %s", user.email)

        messages.success(request, "Email verified! You can now log in.")
        return redirect("accounts:login")


class ResendVerificationEmailView(FormView):
    """Allow users to request a new verification email (rate limited)."""

    template_name = "accounts/verify_email_resend.html"

    @method_decorator(ratelimit(key="ip", rate="3/m", method="POST", block=True))
    def post(self, request, *args, **kwargs):
        email = request.POST.get("email", "").strip()
        success_msg = (
            "If that address is registered and unverified, "
            "we have sent a new verification link."
        )

        try:
            user = User.objects.get(email=User.objects.normalize_email(email))
            if not user.is_verified:
                send_verification_email(request, user)
                logger.info("Verification email resent to %s", user.email)
        except User.DoesNotExist:
            pass

        messages.success(request, success_msg)
        return redirect("accounts:login")

    def get(self, request, *args, **kwargs):
        return render(request, "accounts/verify_email_resend.html")