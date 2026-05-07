"""URL configuration for the shop app."""

from django.urls import path

from shop.views import (
    AddOrRemoveWishlistView,
    ShopProductDetailsView,
    ShopProductListView,
)

app_name = "shop"

urlpatterns = [
    path("products/", ShopProductListView.as_view(), name="products"),
    path("product-details/<slug:slug>/", ShopProductDetailsView.as_view(), name="product-details"),
    path("add-or-remove-whishlist/", AddOrRemoveWishlistView.as_view(), name="add-or-remove-whishlist"),
]