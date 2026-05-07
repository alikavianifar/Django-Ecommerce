"""URL configuration for the cart app."""

from django.urls import path

from cart.views import (
    CartSummaryViews,
    SessionAddProductView,
    SessionRemoveProductView,
    SessionUpdateProductQuantityView,
)

app_name = "cart"

urlpatterns = [
    path("session/add-product/", SessionAddProductView.as_view(), name="session-add-product"),
    path("session/remove-product/", SessionRemoveProductView.as_view(), name="session-remove-product"),
    path("session/update-product-quantity/", SessionUpdateProductQuantityView.as_view(), name="session-update-product-quantity"),
    path("summary/", CartSummaryViews.as_view(), name="cart-summary"),
]