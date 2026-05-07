"""Customer dashboard views: profile, addresses, orders, wishlist, reviews."""

import logging

from django.contrib import messages
from django.contrib.auth import logout, views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import FieldError
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from accounts.models.profiles import Profile
from dashboard.customer.forms import CustomerProfileEditForm, UserAddressForm
from dashboard.permissions import HasCustomerAccessPermission
from order.models import OrderModel, OrderStatusType, UserAddressModel
from review.models import ReviewModel, ReviewStatusType
from shop.models import WishlistModel

logger = logging.getLogger(__name__)

# Allowed fields for the ``?order_by=`` query parameter.
ALLOWED_ADDRESS_ORDER_FIELDS = {"created_date", "-created_date", "city", "-city", "state", "-state"}
ALLOWED_ORDER_ORDER_FIELDS = {"created_date", "-created_date", "total_price", "-total_price", "status", "-status"}


class CustomerDashboardHomeView(LoginRequiredMixin, HasCustomerAccessPermission, SuccessMessageMixin, TemplateView):
    """Customer dashboard landing page with personal account overview."""

    template_name = "dashboard/customer/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        from django.db.models import Sum

        # --- Order Stats ---
        my_orders = OrderModel.objects.filter(user=user)
        context["total_orders"] = my_orders.count()
        context["orders_pending"] = my_orders.filter(status=OrderStatusType.pending.value).count()
        context["orders_success"] = my_orders.filter(status=OrderStatusType.success.value).count()
        context["orders_failed"] = my_orders.filter(status=OrderStatusType.failed.value).count()
        context["total_spent"] = (
            my_orders.filter(status=OrderStatusType.success.value)
            .aggregate(total=Sum("total_price"))["total"] or 0
        )

        # --- Recent Orders (last 5) ---
        context["recent_orders"] = my_orders[:5]

        # --- Wishlist ---
        context["wishlist_count"] = WishlistModel.objects.filter(user=user).count()
        context["wishlist_recent"] = (
            WishlistModel.objects.filter(user=user)
            .select_related("product")
            .order_by("-id")[:4]
        )

        # --- Reviews ---
        my_reviews = ReviewModel.objects.filter(user=user)
        context["reviews_total"] = my_reviews.count()
        context["reviews_accepted"] = my_reviews.filter(status=ReviewStatusType.accepted.value).count()
        context["reviews_pending"] = my_reviews.filter(status=ReviewStatusType.pending.value).count()

        # --- Addresses ---
        context["addresses_count"] = UserAddressModel.objects.filter(user=user).count()

        return context


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class CustomerPersonalInformationdView(LoginRequiredMixin, HasCustomerAccessPermission, SuccessMessageMixin, UpdateView):
    """Edit customer profile information."""

    template_name = "dashboard/customer/settings/personal-information.html"
    form_class = CustomerProfileEditForm
    success_url = reverse_lazy("dashboard:customer:settings-personal-information")
    success_message = "Your profile changes have been saved successfully!"

    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)


class CustomerChangePasswordView(LoginRequiredMixin, HasCustomerAccessPermission, auth_views.PasswordChangeView):
    """Change password for customer (logs out after success)."""

    template_name = "dashboard/customer/settings/change-password.html"

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your password has been updated successfully!")
        logout(self.request)
        return redirect("accounts:login")

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return redirect("dashboard:customer:settings-change-password")


class CustomerProfileEditImageView(LoginRequiredMixin, HasCustomerAccessPermission, SuccessMessageMixin, UpdateView):
    """Update the customer profile image (POST only)."""

    http_method_names = ["post"]
    model = Profile
    fields = ["image"]
    success_url = reverse_lazy("dashboard:customer:settings-personal-information")
    success_message = "Your profile image has been changed successfully!"

    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)

    def form_invalid(self, form):
        messages.error(self.request, "Your profile image could not be changed. Please try again.")
        return redirect(self.success_url)


# ---------------------------------------------------------------------------
# Addresses
# ---------------------------------------------------------------------------

class CustomerAddressCreateView(LoginRequiredMixin, HasCustomerAccessPermission, SuccessMessageMixin, CreateView):
    """Create a new shipping address."""

    template_name = "dashboard/customer/addresses/address-create.html"
    form_class = UserAddressForm
    success_message = "Address submitted successfully. You can now edit its details."

    def get_queryset(self):
        return UserAddressModel.objects.filter(user=self.request.user)

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url:
            self.success_message = "Address submitted successfully."
            return next_url
        return reverse_lazy("dashboard:customer:addresses-list")


class CustomerAddressesListView(LoginRequiredMixin, HasCustomerAccessPermission, ListView):
    """List all addresses belonging to the authenticated customer."""

    template_name = "dashboard/customer/addresses/addresses-list.html"

    def get_queryset(self):
        queryset = UserAddressModel.objects.filter(user=self.request.user)
        if order_by := self.request.GET.get("order_by"):
            if order_by in ALLOWED_ADDRESS_ORDER_FIELDS:
                queryset = queryset.order_by(order_by)
        return queryset


class CustomerAddressEditView(LoginRequiredMixin, HasCustomerAccessPermission, SuccessMessageMixin, UpdateView):
    """Edit an existing shipping address."""

    template_name = "dashboard/customer/addresses/address-edit.html"
    form_class = UserAddressForm
    success_message = "The address has been updated successfully."

    def get_queryset(self):
        return UserAddressModel.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy("dashboard:customer:addresses-list")


class CustomerAddressDeleteView(LoginRequiredMixin, HasCustomerAccessPermission, SuccessMessageMixin, DeleteView):
    """Delete a shipping address."""

    template_name = "dashboard/customer/addresses/address-delete.html"
    success_url = reverse_lazy("dashboard:customer:addresses-list")
    success_message = "The address has been deleted successfully."

    def get_queryset(self):
        return UserAddressModel.objects.filter(user=self.request.user)


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

class CustomerOrdersListView(LoginRequiredMixin, HasCustomerAccessPermission, ListView):
    """Paginated, filterable list of customer orders."""

    template_name = "dashboard/customer/orders/orders.html"
    paginate_by = 5

    def get_paginate_by(self, queryset):
        return self.request.GET.get("page_size", self.paginate_by)

    def get_queryset(self):
        queryset = OrderModel.objects.filter(user=self.request.user)
        if search_q := self.request.GET.get("q"):
            queryset = queryset.filter(
                Q(id__icontains=search_q)
                | Q(address__icontains=search_q)
                | Q(city__icontains=search_q)
                | Q(state__icontains=search_q)
                | Q(zip_code__icontains=search_q)
            )
        if status := self.request.GET.get("status"):
            queryset = queryset.filter(status=status)
        if order_by := self.request.GET.get("order_by"):
            if order_by in ALLOWED_ORDER_ORDER_FIELDS:
                queryset = queryset.order_by(order_by)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_items"] = self.get_queryset().count()
        return context


class CustomerOrderInvoiceDetailView(LoginRequiredMixin, HasCustomerAccessPermission, DetailView):
    """Invoice view for a successful customer order."""

    template_name = "dashboard/customer/orders/order-invoice.html"

    def get_queryset(self):
        return OrderModel.objects.filter(status=OrderStatusType.success.value)


# ---------------------------------------------------------------------------
# Wishlist
# ---------------------------------------------------------------------------

class CustomerWishlistListView(LoginRequiredMixin, HasCustomerAccessPermission, ListView):
    """Paginated wishlist for the authenticated customer."""

    template_name = "dashboard/customer/wishlist/wishlist.html"
    paginate_by = 6

    def get_paginate_by(self, queryset):
        return self.request.GET.get("page_size", self.paginate_by)

    def get_queryset(self):
        queryset = WishlistModel.objects.filter(user=self.request.user)
        if search_q := self.request.GET.get("q"):
            queryset = queryset.filter(product__title__icontains=search_q)
        if order_by := self.request.GET.get("order_by"):
            if order_by in {"created_date", "-created_date"}:
                queryset = queryset.order_by(order_by)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_items"] = self.get_queryset().count()
        return context


class CustomerWishlistDeleteView(LoginRequiredMixin, HasCustomerAccessPermission, SuccessMessageMixin, DeleteView):
    """Remove a product from the wishlist."""

    http_method_names = ["post"]
    success_url = reverse_lazy("dashboard:customer:wishlist")
    success_message = "Product removed from the wishlist."

    def get_queryset(self):
        return WishlistModel.objects.filter(user=self.request.user)


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

class CustomerReviewsListView(LoginRequiredMixin, HasCustomerAccessPermission, ListView):
    """List all reviews submitted by the authenticated customer."""

    template_name = "dashboard/customer/reviews/reviews.html"
    paginate_by = 5

    def get_paginate_by(self, queryset):
        return self.request.GET.get("page_size", self.paginate_by)

    def get_queryset(self):
        return ReviewModel.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_items"] = self.get_queryset().count()
        return context