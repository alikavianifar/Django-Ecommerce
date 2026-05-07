"""Comprehensive tests for the accounts app."""

from django.test import TestCase, Client
from django.urls import reverse

from accounts.forms import AuthenticationForm, RegisterForm
from accounts.models.users import User, UserType
from accounts.models.profiles import Profile
from accounts.tokens import make_verification_token, verify_verification_token


class UserModelTest(TestCase):
    """Tests for the custom User model and UserManager."""

    def test_create_user(self):
        user = User.objects.create_user(email="user@test.com", password="TestPass123!")
        self.assertEqual(user.email, "user@test.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_verified)
        self.assertEqual(user.type, UserType.customer.value)

    def test_create_superuser(self):
        user = User.objects.create_superuser(email="admin@test.com", password="AdminPass123!")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_verified)
        self.assertEqual(user.type, UserType.superuser.value)

    def test_create_user_without_email_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="TestPass123!")

    def test_user_str(self):
        user = User.objects.create_user(email="str@test.com", password="TestPass123!")
        self.assertEqual(str(user), "str@test.com")

    def test_email_is_unique(self):
        User.objects.create_user(email="dup@test.com", password="TestPass123!")
        with self.assertRaises(Exception):
            User.objects.create_user(email="dup@test.com", password="TestPass456!")


class ProfileSignalTest(TestCase):
    """Tests that a Profile is auto-created when a User is created."""

    def test_profile_created_on_user_creation(self):
        user = User.objects.create_user(email="profile@test.com", password="TestPass123!")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_default_fullname(self):
        user = User.objects.create_user(email="name@test.com", password="TestPass123!")
        self.assertEqual(user.user_profile.get_fullname(), "New Client")

    def test_profile_custom_fullname(self):
        user = User.objects.create_user(email="name2@test.com", password="TestPass123!")
        profile = user.user_profile
        profile.first_name = "Ali"
        profile.last_name = "K"
        profile.save()
        self.assertEqual(profile.get_fullname(), "Ali K")


class RegisterFormTest(TestCase):
    """Tests for the registration form validation and save."""

    def _form_data(self, **overrides):
        data = {
            "email": "new@test.com",
            "password": "VeryStr0ng!Pass",
            "password_confirm": "VeryStr0ng!Pass",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "+14155552671",
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = RegisterForm(data=self._form_data())
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        form = RegisterForm(data=self._form_data(password_confirm="Wrong123!"))
        self.assertFalse(form.is_valid())
        self.assertIn("password_confirm", form.errors)

    def test_duplicate_email(self):
        User.objects.create_user(email="new@test.com", password="TestPass123!")
        form = RegisterForm(data=self._form_data())
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_save_creates_user_and_profile(self):
        form = RegisterForm(data=self._form_data())
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.email, "new@test.com")
        self.assertFalse(user.is_verified)
        self.assertEqual(user.user_profile.first_name, "Test")


class AuthenticationFormTest(TestCase):
    """Tests for the custom login form."""

    def test_unverified_user_rejected(self):
        User.objects.create_user(
            email="unverified@test.com", password="TestPass123!", is_verified=False
        )
        form = AuthenticationForm(data={
            "username": "unverified@test.com",
            "password": "TestPass123!",
        })
        self.assertFalse(form.is_valid())

    def test_verified_user_accepted(self):
        User.objects.create_user(
            email="verified@test.com", password="TestPass123!", is_verified=True
        )
        form = AuthenticationForm(data={
            "username": "verified@test.com",
            "password": "TestPass123!",
        })
        self.assertTrue(form.is_valid())


class TokenTest(TestCase):
    """Tests for verification token creation and validation."""

    def test_valid_token(self):
        user = User.objects.create_user(email="token@test.com", password="TestPass123!")
        token = make_verification_token(user)
        result = verify_verification_token(token)
        self.assertEqual(result, user.pk)

    def test_invalid_token(self):
        result = verify_verification_token("invalid-token")
        self.assertIsNone(result)


class LoginViewTest(TestCase):
    """Tests for the login page."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="login@test.com", password="TestPass123!", is_verified=True
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)

    def test_successful_login(self):
        response = self.client.post(reverse("accounts:login"), {
            "username": "login@test.com",
            "password": "TestPass123!",
        })
        self.assertEqual(response.status_code, 302)

    def test_wrong_password(self):
        response = self.client.post(reverse("accounts:login"), {
            "username": "login@test.com",
            "password": "WrongPass!",
        })
        self.assertEqual(response.status_code, 200)


class RegisterViewTest(TestCase):
    """Tests for the registration page."""

    def test_register_page_loads(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)

    def test_successful_registration(self):
        response = self.client.post(reverse("accounts:register"), {
            "email": "reg@test.com",
            "password": "VeryStr0ng!Pass",
            "password_confirm": "VeryStr0ng!Pass",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "+14155552671",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email="reg@test.com").exists())


class VerifyEmailTest(TestCase):
    """Tests for the email verification flow."""

    def test_valid_token_verifies_user(self):
        user = User.objects.create_user(
            email="verify@test.com", password="TestPass123!", is_verified=False
        )
        token = make_verification_token(user)
        response = self.client.get(
            reverse("accounts:verify-email-confirm", kwargs={"token": token})
        )
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    def test_invalid_token_redirects(self):
        response = self.client.get(
            reverse("accounts:verify-email-confirm", kwargs={"token": "bad-token"})
        )
        self.assertEqual(response.status_code, 302)
