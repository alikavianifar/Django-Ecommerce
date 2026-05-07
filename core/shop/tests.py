"""Comprehensive tests for the shop app."""

from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from accounts.models.users import User
from shop.models import Brand, Category, Product, ProductImage, ProductStatus, WishlistModel


class BrandModelTest(TestCase):
    """Tests for the Brand model."""

    def test_create_brand(self):
        brand = Brand.objects.create(name="Nike", slug="nike")
        self.assertEqual(str(brand), "Nike")
        self.assertEqual(brand.slug, "nike")


class CategoryModelTest(TestCase):
    """Tests for the Category model."""

    def test_create_category(self):
        cat = Category.objects.create(title="Shoes", slug="shoes")
        self.assertEqual(str(cat), "Shoes")


class ProductModelTest(TestCase):
    """Tests for the Product model."""

    def setUp(self):
        self.user = User.objects.create_user(email="shop@test.com", password="TestPass123!")
        self.brand = Brand.objects.create(name="TestBrand", slug="testbrand")
        self.category = Category.objects.create(title="TestCat", slug="testcat")
        self.product = Product.objects.create(
            user=self.user,
            brand=self.brand,
            title="Test Product",
            slug="test-product",
            description="A test product",
            stock=10,
            price=Decimal("100.00"),
            discount=20,
            status=ProductStatus.publish.value,
        )
        self.product.category.add(self.category)

    def test_str(self):
        self.assertEqual(str(self.product), "Test Product")

    def test_get_price_with_discount(self):
        self.assertEqual(self.product.get_price(), Decimal("80.00"))

    def test_get_price_no_discount(self):
        self.product.discount = 0
        self.product.save()
        self.assertEqual(self.product.get_price(), Decimal("100.00"))

    def test_is_discounted(self):
        self.assertTrue(self.product.is_discounted())

    def test_not_discounted(self):
        self.product.discount = 0
        self.assertFalse(self.product.is_discounted())

    def test_is_published(self):
        self.assertTrue(self.product.is_published())

    def test_full_stars(self):
        self.product.avg_rate = 4.7
        self.assertEqual(self.product.full_stars, 4)

    def test_has_half_star(self):
        self.product.avg_rate = 4.5
        self.assertTrue(self.product.has_half_star)

    def test_no_half_star(self):
        self.product.avg_rate = 4.3
        self.assertFalse(self.product.has_half_star)


class ProductImageTest(TestCase):
    """Tests for the ProductImage model."""

    def test_create_product_image(self):
        user = User.objects.create_user(email="img@test.com", password="TestPass123!")
        product = Product.objects.create(
            user=user, title="Img Product", slug="img-product",
            description="Test", stock=5, price=Decimal("50.00"),
            status=ProductStatus.publish.value,
        )
        img = ProductImage.objects.create(product=product, order=1)
        self.assertEqual(img.product, product)
        self.assertEqual(img.order, 1)


class ProductListViewTest(TestCase):
    """Tests for the shop product listing page."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email="list@test.com", password="TestPass123!")
        self.category = Category.objects.create(title="Cat1", slug="cat1")
        for i in range(3):
            p = Product.objects.create(
                user=self.user, title=f"Product {i}", slug=f"product-{i}",
                description="Test", stock=5, price=Decimal("50.00"),
                status=ProductStatus.publish.value,
            )
            p.category.add(self.category)

    def test_page_loads(self):
        response = self.client.get(reverse("shop:products"))
        self.assertEqual(response.status_code, 200)

    def test_search_filter(self):
        response = self.client.get(reverse("shop:products"), {"q": "Product 1"})
        self.assertEqual(response.status_code, 200)

    def test_category_filter(self):
        response = self.client.get(reverse("shop:products"), {"category_id": self.category.id})
        self.assertEqual(response.status_code, 200)

    def test_order_by_price(self):
        response = self.client.get(reverse("shop:products"), {"order_by": "price"})
        self.assertEqual(response.status_code, 200)

    def test_invalid_order_by_ignored(self):
        response = self.client.get(reverse("shop:products"), {"order_by": "password"})
        self.assertEqual(response.status_code, 200)


class ProductDetailViewTest(TestCase):
    """Tests for the product detail page."""

    def setUp(self):
        self.user = User.objects.create_user(email="detail@test.com", password="TestPass123!")
        self.product = Product.objects.create(
            user=self.user, title="Detail Product", slug="detail-product",
            description="Test", stock=5, price=Decimal("50.00"),
            status=ProductStatus.publish.value,
        )

    def test_page_loads(self):
        response = self.client.get(
            reverse("shop:product-details", kwargs={"slug": "detail-product"})
        )
        self.assertEqual(response.status_code, 200)

    def test_draft_product_404(self):
        draft = Product.objects.create(
            user=self.user, title="Draft", slug="draft-product",
            description="Test", stock=5, price=Decimal("50.00"),
            status=ProductStatus.draft.value,
        )
        response = self.client.get(
            reverse("shop:product-details", kwargs={"slug": "draft-product"})
        )
        self.assertEqual(response.status_code, 404)


class WishlistViewTest(TestCase):
    """Tests for the wishlist toggle."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="wish@test.com", password="TestPass123!", is_verified=True
        )
        self.product = Product.objects.create(
            user=self.user, title="Wish Product", slug="wish-product",
            description="Test", stock=5, price=Decimal("50.00"),
            status=ProductStatus.publish.value,
        )
        self.client = Client()
        self.client.login(username="wish@test.com", password="TestPass123!")

    def test_add_to_wishlist(self):
        response = self.client.post(
            reverse("shop:add-or-remove-whishlist"),
            {"product_id": self.product.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(WishlistModel.objects.filter(user=self.user, product=self.product).exists())

    def test_remove_from_wishlist(self):
        WishlistModel.objects.create(user=self.user, product=self.product)
        self.client.post(
            reverse("shop:add-or-remove-whishlist"),
            {"product_id": self.product.id},
        )
        self.assertFalse(WishlistModel.objects.filter(user=self.user, product=self.product).exists())
