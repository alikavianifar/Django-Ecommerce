"""Authentication and registration forms.

Includes a custom login form that checks email verification status,
and a standalone registration form with full field validation.
"""

from django import forms
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models.users import User
from accounts.validators import validate_phone_number


class AuthenticationForm(auth_forms.AuthenticationForm):
    """Custom login form that enforces email-based login and ``is_verified``.

    Django's parent already checks ``is_active``, so we only add
    the ``is_verified`` check.
    """

    error_messages = {
        **auth_forms.AuthenticationForm.error_messages,
        "not_verified": "Your account has not been verified yet. "
                        "Please check your email for the verification link.",
    }

    def confirm_login_allowed(self, user):
        """Reject login if the user's email has not been verified."""
        super().confirm_login_allowed(user)

        if not user.is_verified:
            raise ValidationError(
                self.error_messages["not_verified"],
                code="not_verified",
            )


class RegisterForm(forms.Form):
    """Standalone registration form.

    Not a ``ModelForm`` so we have full control over every field and
    no hidden field collision with the User model.  Saving is done
    explicitly inside an atomic transaction.
    """

    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        validators=[validate_password],
        strip=False,
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
    )
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    phone_number = forms.CharField(
        max_length=15,
        validators=[validate_phone_number],
    )

    def clean_email(self):
        """Normalise and de-duplicate the email address.

        Uses a deliberately vague error message to prevent
        email-enumeration attacks.
        """
        email = self.cleaned_data.get("email", "").strip()

        if not email:
            raise ValidationError("Email is required.")

        email = User.objects.normalize_email(email)

        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "If this email address is not already registered, "
                "you will receive a verification link shortly."
            )

        return email

    def clean(self):
        """Verify that both password fields match."""
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Passwords do not match.")

        return cleaned_data

    def save(self):
        """Create the User and update the auto-created Profile atomically.

        Raises ``ValidationError`` on a race-condition duplicate
        (extremely rare after ``clean_email``, but safe to handle).
        """
        with transaction.atomic():
            user = User.objects.create_user(
                email=self.cleaned_data["email"],
                password=self.cleaned_data["password"],
                is_active=True,
                is_verified=False,
            )

            profile = user.user_profile
            profile.first_name = self.cleaned_data["first_name"]
            profile.last_name = self.cleaned_data["last_name"]
            profile.phone_number = self.cleaned_data["phone_number"]
            profile.save()

        return user