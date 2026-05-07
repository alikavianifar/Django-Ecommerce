"""Views for session-based cart operations (add, remove, update, summary)."""

from decimal import Decimal, ROUND_HALF_UP

from django.http import JsonResponse
from django.views.generic import View, TemplateView

from shop.models import Product, ProductStatus
from .cart import CartSession


class SessionAddProductView(View):
    """Add a product to the session cart via AJAX POST."""

    def post(self, request, *args, **kwargs):
        cart = CartSession(request.session)
        product_id = request.POST.get("product_id")
        if product_id:
            cart.add_product(product_id)
        if request.user.is_authenticated:
            cart.merge_session_cart_in_db(request.user)
        return JsonResponse({
            "cart": cart.get_cart_dict(),
            "total_quantity": cart.get_total_quantity(),
        })


class CartSummaryViews(TemplateView):
    """Render the full cart summary page with totals and tax."""

    template_name = "cart/cart-summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = CartSession(self.request.session)
        cart_items = cart.get_cart_items()
        context["cart_items"] = cart_items
        context["total_quantity"] = cart.get_total_quantity()
        context["total_discount"] = cart.get_total_discount()
        total_price = cart.get_total_payment_amount()
        context["total_price"] = total_price
        total_tax = (total_price * Decimal("0.10")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        context["total_tax"] = total_tax
        final_price = (total_price + total_tax).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        context["final_price"] = final_price
        return context


class SessionUpdateProductQuantityView(View):
    """Update the quantity of a product in the session cart via AJAX POST."""

    def post(self, request, *args, **kwargs):
        cart = CartSession(request.session)
        product_id = request.POST.get("product_id")
        quantity = request.POST.get("quantity")
        if product_id and quantity:
            cart.update_product_quantity(product_id, quantity)
        if request.user.is_authenticated:
            cart.merge_session_cart_in_db(request.user)
        return JsonResponse({
            "cart": cart.get_cart_dict(),
            "total_quantity": cart.get_total_quantity(),
        })


class SessionRemoveProductView(View):
    """Remove a product from the session cart via AJAX POST."""

    def post(self, request, *args, **kwargs):
        cart = CartSession(request.session)
        product_id = request.POST.get("product_id")
        if product_id:
            cart.remove_product(product_id)
        if request.user.is_authenticated:
            cart.merge_session_cart_in_db(request.user)
        return JsonResponse({
            "cart": cart.get_cart_dict(),
            "total_quantity": cart.get_total_quantity(),
        })