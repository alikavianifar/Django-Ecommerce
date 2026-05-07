"""Comprehensive tests for the order app."""

from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from accounts.models.users import User
from cart.models import CartModel, CartItemModel
from order.forms import CheckOutForm
from order.models import (
    CouponModel, OrderItemModel, OrderModel, OrderStatusType, UserAddressModel,
)
from shop.models import Product, ProductStatus


class OrderModelTest(TestCase):
    """Tests for OrderModel."""

    def setUp(self):
        self.user = User.objects.create_user(email="order@test.com", password="TestPass123!")
        self.product = Product.objects.create(
            user=self.user, title="Order Product", slug="order-product",
            description="Test", stock=10, price=Decimal("100.00"),
            discount=0, status=ProductStatus.publish.value,
        )

    def test_create_order(self):
        order = OrderModel.objects.create(
            user=self.user, address="123 St", state="CA", city="LA", zip_code="90001",
        )
        self.assertEqual(order.status, OrderStatusType.pending.value)
        self.assertEqual(str(order), f"order@test.com - {order.id}")

    def test_calculate_total_price(self):
        order = OrderModel.objects.create(
            user=self.user, address="123 St", state="CA", city="LA", zip_code="90001",
        )
        OrderItemModel.objects.create(order=order, product=self.product, quantity=2, price=Decimal("100.00"))
        self.assertEqual(order.calculate_total_price(), Decimal("200.00"))

    def test_get_full_address(self):
        order = OrderModel.objects.create(
            user=self.user, address="123 St", state="CA", city="LA", zip_code="90001",
        )
        self.assertEqual(order.get_full_address(), "123 St, CA / LA")

    def test_is_successful(self):
        order = OrderModel.objects.create(
            user=self.user, address="123 St", state="CA", city="LA", zip_code="90001",
            status=OrderStatusType.success.value,
        )
        self.assertTrue(order.is_successful)

    def test_order_item_unit_price(self):
        order = OrderModel.objects.create(
            user=self.user, address="123 St", state="CA", city="LA", zip_code="90001",
        )
        item = OrderItemModel.objects.create(order=order, product=self.product, quantity=3, price=Decimal("50.00"))
        self.assertEqual(item.unit_price, Decimal("150.00"))


class CouponModelTest(TestCase):
    """Tests for CouponModel."""

    def test_create_coupon(self):
        coupon = CouponModel.objects.create(code="SAVE10", discount_percent=10)
        self.assertEqual(str(coupon), "SAVE10")
        self.assertEqual(coupon.discount_percent, 10)

    def test_coupon_usage_tracking(self):
        user = User.objects.create_user(email="coupon@test.com", password="TestPass123!")
        coupon = CouponModel.objects.create(code="USE1", discount_percent=5, max_limit_usage=1)
        coupon.used_by.add(user)
        self.assertEqual(coupon.used_by.count(), 1)


class UserAddressModelTest(TestCase):
    """Tests for UserAddressModel."""

    def test_create_address(self):
        user = User.objects.create_user(email="addr@test.com", password="TestPass123!")
        addr = UserAddressModel.objects.create(
            user=user, address="456 Ave", state="NY", city="NYC", zip_code="10001",
        )
        self.assertEqual(addr.user, user)
        self.assertEqual(addr.city, "NYC")


class CheckOutFormTest(TestCase):
    """Tests for checkout form validation."""

    def setUp(self):
        self.user = User.objects.create_user(email="co@test.com", password="TestPass123!")
        self.address = UserAddressModel.objects.create(
            user=self.user, address="789 Rd", state="TX", city="Dallas", zip_code="75001",
        )

    def _make_request(self):
        class FakeRequest:
            user = self.user
        return FakeRequest()

    def test_valid_form(self):
        form = CheckOutForm(
            data={"address_id": self.address.id, "coupon": ""},
            request=self._make_request(),
        )
        self.assertTrue(form.is_valid())

    def test_invalid_address(self):
        form = CheckOutForm(
            data={"address_id": 99999, "coupon": ""},
            request=self._make_request(),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("address_id", form.errors)

    def test_expired_coupon(self):
        coupon = CouponModel.objects.create(
            code="EXPIRED", discount_percent=10,
            expiration_date=timezone.now() - timedelta(days=1),
        )
        form = CheckOutForm(
            data={"address_id": self.address.id, "coupon": "EXPIRED"},
            request=self._make_request(),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("coupon", form.errors)

    def test_nonexistent_coupon(self):
        form = CheckOutForm(
            data={"address_id": self.address.id, "coupon": "NOTREAL"},
            request=self._make_request(),
        )
        self.assertFalse(form.is_valid())

    def test_already_used_coupon(self):
        coupon = CouponModel.objects.create(code="USED", discount_percent=10)
        coupon.used_by.add(self.user)
        form = CheckOutForm(
            data={"address_id": self.address.id, "coupon": "USED"},
            request=self._make_request(),
        )
        self.assertFalse(form.is_valid())
