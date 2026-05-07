"""Comprehensive tests for the review app."""

from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from accounts.models.users import User
from review.forms import SubmitReviewForm
from review.models import ReviewModel, ReviewStatusType
from shop.models import Product, ProductStatus


class ReviewModelTest(TestCase):
    """Tests for ReviewModel and the avg_rate signal."""

    def setUp(self):
        self.user = User.objects.create_user(email="review@test.com", password="TestPass123!")
        self.product = Product.objects.create(
            user=self.user, title="Review Product", slug="review-product",
            description="Test", stock=10, price=Decimal("100.00"),
            status=ProductStatus.publish.value,
        )

    def test_create_review(self):
        review = ReviewModel.objects.create(
            user=self.user, product=self.product, description="Great!", rate=5,
        )
        self.assertEqual(str(review), f"{self.user} - {self.product.id}")
        self.assertEqual(review.status, ReviewStatusType.pending.value)

    def test_avg_rate_calculated_on_accept(self):
        ReviewModel.objects.create(
            user=self.user, product=self.product, description="Good", rate=4,
            status=ReviewStatusType.accepted.value,
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.avg_rate, 4.0)

    def test_avg_rate_with_multiple_reviews(self):
        user2 = User.objects.create_user(email="r2@test.com", password="TestPass123!")
        ReviewModel.objects.create(
            user=self.user, product=self.product, description="OK", rate=3,
            status=ReviewStatusType.accepted.value,
        )
        ReviewModel.objects.create(
            user=user2, product=self.product, description="Great", rate=5,
            status=ReviewStatusType.accepted.value,
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.avg_rate, 4.0)

    def test_pending_review_does_not_affect_avg(self):
        ReviewModel.objects.create(
            user=self.user, product=self.product, description="Pending", rate=1,
            status=ReviewStatusType.pending.value,
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.avg_rate, 0.0)

    def test_get_status(self):
        review = ReviewModel.objects.create(
            user=self.user, product=self.product, description="Test", rate=5,
        )
        status = review.get_status()
        self.assertEqual(status["title"], "pending")


class SubmitReviewFormTest(TestCase):
    """Tests for the review submission form."""

    def setUp(self):
        self.user = User.objects.create_user(email="rf@test.com", password="TestPass123!")
        self.product = Product.objects.create(
            user=self.user, title="Form Product", slug="form-product",
            description="Test", stock=10, price=Decimal("100.00"),
            status=ProductStatus.publish.value,
        )

    def test_valid_form(self):
        form = SubmitReviewForm(data={
            "product": self.product.id,
            "rate": 4,
            "description": "Very good product!",
        })
        self.assertTrue(form.is_valid())

    def test_missing_description(self):
        form = SubmitReviewForm(data={
            "product": self.product.id,
            "rate": 4,
            "description": "",
        })
        self.assertFalse(form.is_valid())

    def test_draft_product_rejected(self):
        draft = Product.objects.create(
            user=self.user, title="Draft", slug="draft-rev",
            description="Test", stock=10, price=Decimal("100.00"),
            status=ProductStatus.draft.value,
        )
        form = SubmitReviewForm(data={
            "product": draft.id,
            "rate": 5,
            "description": "Should fail",
        })
        self.assertFalse(form.is_valid())


class SubmitReviewViewTest(TestCase):
    """Tests for the review submission view."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="rv@test.com", password="TestPass123!", is_verified=True
        )
        self.product = Product.objects.create(
            user=self.user, title="View Product", slug="view-product",
            description="Test", stock=10, price=Decimal("100.00"),
            status=ProductStatus.publish.value,
        )
        self.client = Client()
        self.client.login(username="rv@test.com", password="TestPass123!")

    def test_submit_review(self):
        response = self.client.post(reverse("review:submit-review"), {
            "product": self.product.id,
            "rate": 5,
            "description": "Excellent product!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ReviewModel.objects.filter(user=self.user, product=self.product).exists())

    def test_anonymous_user_redirected(self):
        self.client.logout()
        response = self.client.post(reverse("review:submit-review"), {
            "product": self.product.id,
            "rate": 5,
            "description": "Should redirect",
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
