"""URL configuration for the admin dashboard."""

from django.urls import path

from dashboard.admin.views import (
    AdminBrandQuickCreateView,
    AdminCategoryQuickCreateView,
    AdminChangePasswordView,
    AdminCouponCreateView,
    AdminCouponDeleteView,
    AdminCouponEditView,
    AdminCouponListView,
    AdminCustomerDetailView,
    AdminCustomerEditView,
    AdminCustomersListView,
    AdminCustomerToggleActiveView,
    AdminCustomerToggleVerifiedView,
    AdminDashboardHomeView,
    AdminDashboardOrdersListView,
    AdminOrderDetailView,
    AdminOrderInvoiceDetailView,
    AdminPersonalInformationdView,
    AdminProductCreateView,
    AdminProductDeleteView,
    AdminProductEditView,
    AdminProductsListView,
    AdminProfileEditImageView,
    AdminReviewEditView,
    AdminReviewListView,
    admin_export_coupons_csv,
    admin_export_customers_csv,
    admin_export_messages_csv,
    admin_export_orders_csv,
    admin_export_products_csv,
    admin_delete_message,
    AdminMessageDetailView,
    AdminMessagesListView,
)

app_name = "admin"

urlpatterns = [
    path("home/", AdminDashboardHomeView.as_view(), name="home"),

    # Product
    path("product/create", AdminProductCreateView.as_view(), name="product-create"),
    path("products/list", AdminProductsListView.as_view(), name="products-list"),
    path("product/<int:pk>/edit/", AdminProductEditView.as_view(), name="product-edit"),
    path("product/<int:pk>/delete/", AdminProductDeleteView, name="product-delete"),

    # New brand and category
    path("products/brand/quick-create/", AdminBrandQuickCreateView, name="brand-quick-create"),
    path("products/category/quick-create/", AdminCategoryQuickCreateView, name="category-quick-create"),

    # Orders
    path("orders/list/", AdminDashboardOrdersListView.as_view(), name="orders-list"),
    path("order/<int:pk>/detail/", AdminOrderDetailView.as_view(), name="order-detail"),
    path("order/<int:pk>/invoice/", AdminOrderInvoiceDetailView.as_view(), name="order-invoice"),

    # Coupons
    path("coupons/list/", AdminCouponListView.as_view(), name="coupon-list"),
    path("coupon/create/", AdminCouponCreateView.as_view(), name="coupon-create"),
    path("coupon/<int:pk>/edit/", AdminCouponEditView.as_view(), name="coupon-edit"),
    path("coupon/<int:pk>/delete/", AdminCouponDeleteView.as_view(), name="coupon-delete"),

    # Settings
    path("settings/profile-image/", AdminProfileEditImageView.as_view(), name="settings-profile-image"),
    path("settings/personal-information/", AdminPersonalInformationdView.as_view(), name="settings-personal-information"),
    path("settings/change-password/", AdminChangePasswordView.as_view(), name="settings-change-password"),

    # Customers
    path("customers/list/", AdminCustomersListView.as_view(), name="customers-list"),
    path("customer/<int:pk>/detail/", AdminCustomerDetailView.as_view(), name="customer-detail"),
    path("customer/<int:pk>/edit/", AdminCustomerEditView.as_view(), name="customer-edit"),
    path("customer/<int:pk>/toggle-active/", AdminCustomerToggleActiveView, name="customer-toggle-active"),
    path("customer/<int:pk>/toggle-verified/", AdminCustomerToggleVerifiedView, name="customer-toggle-verified"),

    # Reviews
    path("review/list/", AdminReviewListView.as_view(), name="review-list"),
    path("review/<int:pk>/edit/", AdminReviewEditView.as_view(), name="review-edit"),

    # Messages
    path("messages/list/", AdminMessagesListView.as_view(), name="messages-list"),
    path("message/<int:pk>/detail/", AdminMessageDetailView.as_view(), name="message-detail"),
    path("message/<int:pk>/delete/", admin_delete_message, name="message-delete"),

    # CSV Exports
    path("export/orders/csv/", admin_export_orders_csv, name="export-orders-csv"),
    path("export/customers/csv/", admin_export_customers_csv, name="export-customers-csv"),
    path("export/products/csv/", admin_export_products_csv, name="export-products-csv"),
    path("export/coupons/csv/", admin_export_coupons_csv, name="export-coupons-csv"),
    path("export/messages/csv/", admin_export_messages_csv, name="export-messages-csv"),
]