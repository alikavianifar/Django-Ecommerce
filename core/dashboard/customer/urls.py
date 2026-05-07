"""URL configuration for the customer dashboard."""

from django.urls import path

from dashboard.customer.views import (
    CustomerAddressCreateView,
    CustomerAddressDeleteView,
    CustomerAddressEditView,
    CustomerAddressesListView,
    CustomerChangePasswordView,
    CustomerDashboardHomeView,
    CustomerOrderInvoiceDetailView,
    CustomerOrdersListView,
    CustomerPersonalInformationdView,
    CustomerProfileEditImageView,
    CustomerReviewsListView,
    CustomerWishlistDeleteView,
    CustomerWishlistListView,
)

app_name = "customer"

urlpatterns = [
    path("home/", CustomerDashboardHomeView.as_view(), name="home"),

    # Settings
    path("settings/profile-image/", CustomerProfileEditImageView.as_view(), name="settings-profile-image"),
    path("settings/personal-information/", CustomerPersonalInformationdView.as_view(), name="settings-personal-information"),
    path("settings/change-password/", CustomerChangePasswordView.as_view(), name="settings-change-password"),

    # Addresses
    path("address/create", CustomerAddressCreateView.as_view(), name="address-create"),
    path("addresses/list", CustomerAddressesListView.as_view(), name="addresses-list"),
    path("address/<int:pk>/edit/", CustomerAddressEditView.as_view(), name="address-edit"),
    path("address/<int:pk>/delete/", CustomerAddressDeleteView.as_view(), name="address-delete"),

    # Orders
    path("orders", CustomerOrdersListView.as_view(), name="orders"),
    path("order/<int:pk>/invoice/", CustomerOrderInvoiceDetailView.as_view(), name="order-invoice"),

    # Wishlist
    path("wishlist", CustomerWishlistListView.as_view(), name="wishlist"),
    path("wishlist/<int:pk>/delete/", CustomerWishlistDeleteView.as_view(), name="wishlist-delete"),

    # Reviews
    path("reviews", CustomerReviewsListView.as_view(), name="reviews"),
]
