"""Order-related models: addresses, coupons, orders, and order items."""

from decimal import Decimal, ROUND_HALF_UP

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class OrderStatusType(models.IntegerChoices):
    """Possible states of an order."""

    pending = 1, _("pending")
    success = 2, _("success")
    failed = 3, _("failed")


class UserAddressModel(models.Model):
    """A shipping address belonging to a user."""

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    address = models.CharField(max_length=250)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=50)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_date"]


class CouponModel(models.Model):
    """A discount coupon with usage limits and expiration."""

    code = models.CharField(max_length=100)
    discount_percent = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    max_limit_usage = models.PositiveIntegerField(default=10)
    used_by = models.ManyToManyField(
        "accounts.User", related_name="coupon_users", blank=True
    )
    expiration_date = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code


class OrderModel(models.Model):
    """A customer order with address snapshot, payment status, and Stripe IDs."""

    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT)

    # Order address information (snapshot at time of order)
    address = models.CharField(max_length=250)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=50)

    total_price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(
        CouponModel, on_delete=models.PROTECT, null=True, blank=True
    )
    status = models.IntegerField(
        choices=OrderStatusType.choices, default=OrderStatusType.pending.value
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["-created_date"]

    def calculate_total_price(self):
        """Return the sum of (price × quantity) for all order items."""
        return sum(item.price * item.quantity for item in self.order_items.all())

    def calculate_tax_price(self):
        """Return the 10% tax on the order subtotal."""
        return (Decimal(self.calculate_total_price()) * Decimal("0.1")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def __str__(self):
        return f"{self.user.email} - {self.id}"

    def get_status(self):
        """Return a dict with status id, name, and label."""
        return {
            "id": self.status,
            "title": OrderStatusType(self.status).name,
            "label": OrderStatusType(self.status).label,
        }

    def get_full_address(self):
        """Return a formatted single-line address string."""
        return f"{self.address}, {self.state} / {self.city}"

    @property
    def is_successful(self):
        """Whether this order has been paid successfully."""
        return self.status == OrderStatusType.success.value

    def get_price(self):
        """Alias for ``total_price`` (used in templates)."""
        return self.total_price


class OrderItemModel(models.Model):
    """A single product line inside an order."""

    order = models.ForeignKey(
        OrderModel, on_delete=models.CASCADE, related_name="order_items"
    )
    product = models.ForeignKey("shop.Product", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.title} - {self.order.id}"

    @property
    def unit_price(self):
        """Total price for this line (price × quantity)."""
        return self.price * self.quantity