"""Comprehensive tests for the cart app."""

from decimal import Decimal

from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models.users import User
from cart.cart import CartSession
from cart.models import CartModel, CartItemModel
from shop.models import Product, ProductStatus


class CartSessionTest(TestCase):
    """Tests for the session-based cart logic."""

    def setUp(self):
        self.user = User.objects.create_user(email="cart@test.com", password="TestPass123!")
        self.product = Product.objects.create(
            user=self.user, title="Cart Product", slug="cart-product",
            description="Test", stock=10, price=Decimal("100.00"),
            discount=0, status=ProductStatus.publish.value,
        )
        self.session = SessionStore()
        self.cart = CartSession(self.session)

    def test_add_product(self):
        self.cart.add_product(str(self.product.id))
        self.assertEqual(self.cart.get_total_quantity(), 1)

    def test_add_product_twice_increments(self):
        self.cart.add_product(str(self.product.id))
        self.cart.add_product(str(self.product.id))
        self.assertEqual(self.cart.get_total_quantity(), 2)

    def test_add_product_respects_stock(self):
        self.product.stock = 2
        self.product.save()
        for _ in range(5):
            self.cart.add_product(str(self.product.id))
        self.assertEqual(self.cart.get_total_quantity(), 2)

    def test_remove_product(self):
        self.cart.add_product(str(self.product.id))
        self.cart.remove_product(str(self.product.id))
        self.assertEqual(self.cart.get_total_quantity(), 0)

    def test_update_quantity(self):
        self.cart.add_product(str(self.product.id))
        self.cart.update_product_quantity(str(self.product.id), 5)
        self.assertEqual(self.cart.get_total_quantity(), 5)

    def test_update_quantity_clamps_to_stock(self):
        self.product.stock = 3
        self.product.save()
        self.cart.add_product(str(self.product.id))
        self.cart.update_product_quantity(str(self.product.id), 10)
        self.assertEqual(self.cart.get_total_quantity(), 3)

    def test_update_quantity_minimum_one(self):
        self.cart.add_product(str(self.product.id))
        self.cart.update_product_quantity(str(self.product.id), 0)
        self.assertEqual(self.cart.get_total_quantity(), 1)

    def test_clear(self):
        self.cart.add_product(str(self.product.id))
        self.cart.clear()
        self.assertEqual(self.cart.get_total_quantity(), 0)

    def test_get_cart_items(self):
        self.cart.add_product(str(self.product.id))
        items = self.cart.get_cart_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["product_obj"], self.product)

    def test_get_total_discount(self):
        self.product.discount = 10
        self.product.save()
        self.cart.add_product(str(self.product.id))
        discount = self.cart.get_total_discount()
        self.assertEqual(discount, Decimal("10.00"))


class CartModelTest(TestCase):
    """Tests for the CartModel."""

    def setUp(self):
        self.user = User.objects.create_user(email="cartm@test.com", password="TestPass123!")
        self.product = Product.objects.create(
            user=self.user, title="CM Product", slug="cm-product",
            description="Test", stock=10, price=Decimal("50.00"),
            discount=0, status=ProductStatus.publish.value,
        )

    def test_calculate_total_price(self):
        cart = CartModel.objects.create(user=self.user)
        CartItemModel.objects.create(cart=cart, product=self.product, quantity=3)
        self.assertEqual(cart.calculate_total_price(), Decimal("150.00"))

    def test_cart_str(self):
        cart = CartModel.objects.create(user=self.user)
        self.assertEqual(str(cart), "cartm@test.com")


class CartViewsTest(TestCase):
    """Tests for cart AJAX endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="cartv@test.com", password="TestPass123!", is_verified=True
        )
        self.product = Product.objects.create(
            user=self.user, title="CV Product", slug="cv-product",
            description="Test", stock=10, price=Decimal("50.00"),
            status=ProductStatus.publish.value,
        )
        self.client = Client()

    def test_add_product_anonymous(self):
        response = self.client.post(
            reverse("cart:session-add-product"),
            {"product_id": str(self.product.id)},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_quantity"], 1)

    def test_cart_summary_page(self):
        response = self.client.get(reverse("cart:cart-summary"))
        self.assertEqual(response.status_code, 200)

    def test_remove_product(self):
        self.client.post(reverse("cart:session-add-product"), {"product_id": str(self.product.id)})
        response = self.client.post(
            reverse("cart:session-remove-product"),
            {"product_id": str(self.product.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_quantity"], 0)
