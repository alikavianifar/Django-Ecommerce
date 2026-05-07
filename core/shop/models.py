"""Product catalog models: products, brands, categories, images, wishlists."""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ProductStatus(models.IntegerChoices):
    """Publication status for a product."""

    publish = 1, "publish"
    draft = 2, "draft"


class Brand(models.Model):
    """A product brand (e.g. Nike, Adidas)."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(allow_unicode=True, unique=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    """A product category (e.g. Shoes, Shirts)."""

    title = models.CharField(max_length=255)
    slug = models.SlugField(allow_unicode=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.title


class Product(models.Model):
    """A product available in the store."""

    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    image = models.ImageField(upload_to="product/img/", default="default-product.jpg")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(allow_unicode=True, unique=True)
    description = models.TextField()
    stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    category = models.ManyToManyField(Category)
    status = models.IntegerField(
        choices=ProductStatus.choices, default=ProductStatus.draft.value
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    avg_rate = models.FloatField(default=0.0)

    class Meta:
        ordering = ["-created_date"]

    def __str__(self):
        return self.title

    def get_price(self):
        """Return the final price after applying the discount percentage."""
        discount_factor = Decimal(self.discount) / Decimal("100")
        amount = self.price - (self.price * discount_factor)
        return round(amount, 2)

    def is_discounted(self):
        """Return ``True`` if the product has a non-zero discount."""
        return self.discount != 0

    def is_published(self):
        """Return ``True`` if the product status is *publish*."""
        return self.status == ProductStatus.publish.value

    @property
    def full_stars(self):
        """Number of full stars to render (integer part of avg_rate)."""
        return int(self.avg_rate or 0)

    @property
    def has_half_star(self):
        """Whether a half-star should be rendered."""
        return (self.avg_rate or 0) - int(self.avg_rate or 0) >= 0.5


class ProductImage(models.Model):
    """An additional image for a product."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    file = models.ImageField(upload_to="product/extra-img/")
    order = models.PositiveIntegerField(default=1)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)


class WishlistModel(models.Model):
    """A user's wishlist entry for a single product."""

    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return self.product.title