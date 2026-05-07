from django.urls import path, reverse_lazy
from accounts import views
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    path('login/',views.LoginView.as_view(),name="login"),
    path('logout/',views.LogoutView.as_view(),name="logout"),
    path('register/',views.RegisterView.as_view(),name="register"),

    path("verify-email/sent/",views.VerifyEmailSentView.as_view(),name="verify-email-sent"),
    path("verify-email/resend/",views.ResendVerificationEmailView.as_view(),name="verify-email-resend"),
    path("verify-email/<str:token>/",views.VerifyEmailConfirmView.as_view(),name="verify-email-confirm"),

    path(
        "password/reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/emails/password_reset_email.html",
            html_email_template_name="accounts/emails/password_reset_email.html",
            subject_template_name="accounts/emails/password_reset_subject.txt",
            success_url=reverse_lazy("accounts:password-reset-done"),
            extra_context={"title": "Reset your password"},
        ),
        name="password-reset",
    ),
    path(
        "password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password-reset-done",
    ),
    path(
        "password/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password-reset-complete"),
        ),
        name="password-reset-confirm",
    ),
    path(
        "password/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password-reset-complete",
    ),

]