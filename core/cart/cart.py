"""
Cart session management module.

Provides a session-based shopping cart that stores cart state in the
user's HTTP session and optionally synchronises with the database
when the user is authenticated.
"""

from shop.models import Product, ProductStatus
from cart.models import CartModel, CartItemModel


class CartSession:
    """Session-backed shopping cart.

    Stores a lightweight ``{"items": [...]}`` structure inside
    ``request.session["cart"]`` so that guests can shop without an account.
    When a logged-in user modifies the cart the changes are also
    persisted to :model:`cart.CartModel` / :model:`cart.CartItemModel`.
    """

    total_payment_price = 0

    def __init__(self, session):
        self.session = session
        self._cart = self.session.setdefault("cart", {"items": []})

    def add_product(self, product_id):
        """Add one unit of *product_id* to the cart (respects stock)."""
        product = Product.objects.get(id=product_id, status=ProductStatus.publish.value)

        for item in self._cart["items"]:
            if product_id == item["product_id"]:
                if item["quantity"] < product.stock:
                    item["quantity"] += 1
                else:
                    item["quantity"] = product.stock
                break
        else:
            if product.stock > 0:
                new_item = {"product_id": product_id, "quantity": 1}
                self._cart["items"].append(new_item)

        self.save()

    def save(self):
        """Mark the session as modified so Django persists the change."""
        self.session.modified = True

    def clear(self):
        """Remove every item from the cart."""
        self._cart = self.session["cart"] = {"items": []}
        self.save()

    def get_cart_dict(self):
        """Return the raw cart dictionary stored in the session."""
        return self._cart

    def get_total_quantity(self):
        """Return the sum of quantities across all cart items."""
        total_quantity = 0
        for item in self._cart["items"]:
            total_quantity += item["quantity"]
        return total_quantity

    def get_total_discount(self):
        """Return the total monetary discount across all cart items."""
        total_discount = 0

        for item in self._cart["items"]:
            product = Product.objects.get(
                id=item["product_id"],
                status=ProductStatus.publish.value
            )
            discount_per_unit = product.price - product.get_price()
            total_discount += item["quantity"] * discount_per_unit

        return total_discount

    def get_cart_items(self):
        """Hydrate each cart item with its ``Product`` instance and totals."""
        cart_items = self._cart["items"]
        self.total_payment_price = 0
        for item in cart_items:
            product_obj = Product.objects.get(
                id=item["product_id"], status=ProductStatus.publish.value
            )
            item["product_obj"] = product_obj
            total_price = int(item["quantity"]) * product_obj.get_price()
            item["total_price"] = total_price
            self.total_payment_price += total_price
        return cart_items

    def get_total_payment_amount(self):
        """Return the total payment amount (call after ``get_cart_items``)."""
        return self.total_payment_price

    def update_product_quantity(self, product_id, quantity):
        """Set the quantity for *product_id*, clamped to [1, stock]."""
        product = Product.objects.get(id=product_id, status=ProductStatus.publish.value)
        quantity = int(quantity)

        if quantity > product.stock:
            quantity = product.stock
        elif quantity < 1:
            quantity = 1

        for item in self._cart["items"]:
            if product_id == item["product_id"]:
                item["quantity"] = quantity
                break
        self.save()

    def remove_product(self, product_id):
        """Remove *product_id* from the cart entirely."""
        for item in self._cart["items"]:
            if product_id == item["product_id"]:
                self._cart["items"].remove(item)
                break
        else:
            return
        self.save()

    def sync_cart_items_from_db(self, user):
        """Pull the user's DB cart into the session and merge back."""
        cart, created = CartModel.objects.get_or_create(user=user)
        cart_items = CartItemModel.objects.filter(cart=cart)

        for cart_item in cart_items:
            for item in self._cart["items"]:
                if str(cart_item.product.id) == item["product_id"]:
                    cart_item.quantity = item["quantity"]
                    cart_item.save()
                    break
            else:
                new_item = {
                    "product_id": str(cart_item.product.id),
                    "quantity": cart_item.quantity,
                }
                self._cart["items"].append(new_item)
        self.merge_session_cart_in_db(user)
        self.save()

    def merge_session_cart_in_db(self, user):
        """Persist current session cart items to the database."""
        cart, created = CartModel.objects.get_or_create(user=user)

        for item in self._cart["items"]:
            product_obj = Product.objects.get(
                id=item["product_id"], status=ProductStatus.publish.value
            )
            cart_item, created = CartItemModel.objects.get_or_create(
                cart=cart, product=product_obj
            )
            cart_item.quantity = item["quantity"]
            cart_item.save()

        session_product_ids = [item["product_id"] for item in self._cart["items"]]
        CartItemModel.objects.filter(cart=cart).exclude(
            product__id__in=session_product_ids
        ).delete()
