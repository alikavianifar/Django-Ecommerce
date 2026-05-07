"""Tests for static website pages."""

from django.test import TestCase, Client
from django.urls import reverse


class WebsiteViewsTest(TestCase):
    """Tests for the home, about, and contact pages."""

    def setUp(self):
        self.client = Client()

    def test_home_page(self):
        response = self.client.get(reverse("website:index"))
        self.assertEqual(response.status_code, 200)

    def test_about_page(self):
        response = self.client.get(reverse("website:about"))
        self.assertEqual(response.status_code, 200)

    def test_contact_page(self):
        response = self.client.get(reverse("website:contact"))
        self.assertEqual(response.status_code, 200)
