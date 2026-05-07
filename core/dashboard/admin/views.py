"""Admin dashboard views for product, order, customer, coupon, and review management."""

import csv
import json
import logging
from datetime import timedelta

from django import forms as forms_module

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout, views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import FieldError
from django.db.models import Count, Q, Sum, Avg, F
from cart.models import CartModel
from review.models import ReviewModel, ReviewStatusType
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from accounts.models.profiles import Profile
from accounts.models.users import User, UserType
from dashboard.admin.forms import (
    AdminProfileEditForm,
    CouponForm,
    CustomerEditForm,
    ProductForm,
    ReviewForm,
)
from dashboard.permissions import HasAdminAccessPermission
from order.models import CouponModel, OrderModel, OrderStatusType
from review.models import ReviewModel, ReviewStatusType
from shop.models import Brand, Category, Product, ProductStatus
from website.models import ContactMessage, ContactStatusType

logger = logging.getLogger(__name__)

# Allowed fields for the ``?order_by=`` query parameter.
ALLOWED_ORDER_FIELDS = {"price", "-price", "created_date", "-created_date", "title", "-title"}


class AdminDashboardHomeView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, TemplateView):
    """Admin dashboard landing page with key business metrics."""

    template_name = "dashboard/admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from order.models import OrderItemModel

        # --- Key Stats ---
        all_orders = OrderModel.objects.all()
        success_orders = all_orders.filter(status=OrderStatusType.success.value)
        total_revenue = success_orders.aggregate(total=Sum("total_price"))["total"] or 0

        context["total_revenue"] = total_revenue
        context["total_orders"] = all_orders.count()
        context["total_customers"] = User.objects.filter(type=UserType.customer.value).count()
        context["total_products"] = Product.objects.count()
        context["published_products"] = Product.objects.filter(status=ProductStatus.publish.value).count()

        # --- Order Status Breakdown ---
        context["orders_pending"] = all_orders.filter(status=OrderStatusType.pending.value).count()
        context["orders_success"] = success_orders.count()
        context["orders_failed"] = all_orders.filter(status=OrderStatusType.failed.value).count()

        # --- Advanced Metrics ---
        # Average Order Value (AOV)
        context["average_order_value"] = total_revenue / context["orders_success"] if context["orders_success"] > 0 else 0
        
        # This Month Revenue
        now = timezone.now()
        this_month_orders = success_orders.filter(created_date__year=now.year, created_date__month=now.month)
        context["this_month_revenue"] = this_month_orders.aggregate(total=Sum("total_price"))["total"] or 0
        context["this_month_orders"] = this_month_orders.count()

        # Out of Stock & Coupons
        from django.db.models import Q
        context["out_of_stock_count"] = Product.objects.filter(stock=0).count()
        context["active_coupons_count"] = CouponModel.objects.filter(
            Q(expiration_date__isnull=True) | Q(expiration_date__gte=now)
        ).count()


        # --- Recent Orders (last 5) ---
        context["recent_orders"] = all_orders.select_related("user__user_profile")[:5]

        # --- Top Products (by number of order items) ---
        top_product_ids = (
            OrderItemModel.objects
            .values("product")
            .annotate(order_count=Count("id"))
            .order_by("-order_count")[:5]
        )
        top_ids = [item["product"] for item in top_product_ids]
        top_products_map = {p.id: p for p in Product.objects.filter(id__in=top_ids)}
        context["top_products"] = [
            {"product": top_products_map[item["product"]], "order_count": item["order_count"]}
            for item in top_product_ids
            if item["product"] in top_products_map
        ]

        # --- Recent Customers (last 5) ---
        context["recent_customers"] = (
            User.objects.filter(type=UserType.customer.value)
            .select_related("user_profile")
            .order_by("-created_date")[:5]
        )

        # --- Review Stats ---
        context["reviews_pending"] = ReviewModel.objects.filter(
            status=ReviewStatusType.pending.value
        ).count()
        context["reviews_total"] = ReviewModel.objects.count()

        # --- Contact Messages ---
        unread_messages = ContactMessage.objects.filter(status=ContactStatusType.unread)
        context["messages_unread"] = unread_messages.count()
        context["recent_messages"] = unread_messages.order_by("-created_date")[:5]

        # --- Recent Reviews ---
        context["recent_reviews"] = ReviewModel.objects.filter(status=ReviewStatusType.pending.value).select_related("user__user_profile", "product").order_by("-created_date")[:5]

        # --- Low Stock Products (stock <= 5) ---
        context["low_stock_products"] = (
            Product.objects.filter(stock__lte=5, status=ProductStatus.publish.value)
            .order_by("stock")[:5]
        )

        # --- Chart Data: Monthly Revenue (last 12 months) ---
        twelve_months_ago = timezone.now() - timedelta(days=365)
        monthly_revenue = (
            success_orders.filter(created_date__gte=twelve_months_ago)
            .annotate(month=TruncMonth("created_date"))
            .values("month")
            .annotate(revenue=Sum("total_price"), count=Count("id"))
            .order_by("month")
        )
        chart_labels = []
        chart_revenue = []
        chart_orders = []
        for entry in monthly_revenue:
            chart_labels.append(entry["month"].strftime("%b %Y"))
            chart_revenue.append(float(entry["revenue"] or 0))
            chart_orders.append(entry["count"])
        context["chart_labels"] = json.dumps(chart_labels)
        context["chart_revenue"] = json.dumps(chart_revenue)
        context["chart_orders"] = json.dumps(chart_orders)

        # --- Chart Data: Sales by Category ---
        from django.db.models import F
        category_sales = (
            OrderItemModel.objects.filter(order__status=OrderStatusType.success.value)
            .values("product__category__title")
            .annotate(total_revenue=Sum(F("price") * F("quantity")))
            .order_by("-total_revenue")
        )
        
        cat_labels = []
        cat_data = []
        for cs in category_sales:
            cat_title = cs["product__category__title"]
            if cat_title:
                cat_labels.append(cat_title)
                cat_data.append(float(cs["total_revenue"] or 0))
        
        context["chart_category_labels"] = json.dumps(cat_labels)
        context["chart_category_data"] = json.dumps(cat_data)

        # --- Chart Data: Customer Growth (6 Months) ---
        six_months_ago = timezone.now() - timedelta(days=180)
        monthly_users = (
            User.objects.filter(type=UserType.customer.value, created_date__gte=six_months_ago)
            .annotate(month=TruncMonth("created_date"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        user_labels = []
        user_counts = []
        for entry in monthly_users:
            user_labels.append(entry["month"].strftime("%b %Y"))
            user_counts.append(entry["count"])
        context["chart_user_labels"] = json.dumps(user_labels)
        context["chart_user_counts"] = json.dumps(user_counts)

        # --- Actionable Panels ---
        context["actionable_pending_orders"] = all_orders.filter(status=OrderStatusType.pending.value).select_related("user__user_profile").order_by('created_date')[:5]

        from shop.models import WishlistModel
        context["top_wishlisted"] = (
            WishlistModel.objects.values('product__id', 'product__title', 'product__image')
            .annotate(wish_count=Count('id'))
            .order_by('-wish_count')[:5]
        )

        # --- Advanced Business Intelligence Metrics ---
        # 1. Global Store Rating
        avg_rating = ReviewModel.objects.filter(status=ReviewStatusType.accepted.value).aggregate(Avg('rate'))['rate__avg']
        context["average_store_rating"] = round(avg_rating, 1) if avg_rating else 0.0

        # 2. Cart Abandonment Analytics
        # Carts that have items but are still active (not checked out)
        active_carts = CartModel.objects.annotate(item_count=Count('cart_items')).filter(item_count__gt=0).count()
        total_checkouts = success_orders.count()
        if (active_carts + total_checkouts) > 0:
            abandonment_rate = (active_carts / (active_carts + total_checkouts)) * 100
        else:
            abandonment_rate = 0.0
        context["cart_abandonment_rate"] = round(abandonment_rate, 1)
        context["active_carts_count"] = active_carts

        # 3. Coupon Usage Analytics
        orders_with_coupon = all_orders.filter(coupon__isnull=False).count()
        if context["total_orders"] > 0:
            coupon_usage_rate = (orders_with_coupon / context["total_orders"]) * 100
        else:
            coupon_usage_rate = 0.0
        context["coupon_usage_rate"] = round(coupon_usage_rate, 1)
        context["orders_with_coupon"] = orders_with_coupon

        # --- Chart Data: Order Status (pie chart) ---
        context["chart_status_data"] = json.dumps([
            context["orders_success"],
            context["orders_pending"],
            context["orders_failed"],
        ])

        return context


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class AdminPersonalInformationdView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, UpdateView):
    """Edit admin user profile information."""

    template_name = "dashboard/admin/settings/personal-information.html"
    form_class = AdminProfileEditForm
    success_url = reverse_lazy("dashboard:admin:settings-personal-information")
    success_message = "Your profile changes have been saved successfully!"

    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)


class AdminChangePasswordView(LoginRequiredMixin, HasAdminAccessPermission, auth_views.PasswordChangeView):
    """Change password for admin user (logs out after success)."""

    template_name = "dashboard/admin/settings/change-password.html"

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your password has been updated successfully!")
        logout(self.request)
        return redirect("accounts:login")

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return redirect("dashboard:admin:settings-change-password")


class AdminProfileEditImageView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, UpdateView):
    """Update the admin profile image (POST only)."""

    http_method_names = ["post"]
    model = Profile
    fields = ["image"]
    success_url = reverse_lazy("dashboard:admin:settings-personal-information")
    success_message = "Your profile image has been changed successfully!"

    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)

    def form_invalid(self, form):
        messages.error(self.request, "Your profile image could not be changed. Please try again.")
        return super().form_invalid(form)


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

class AdminProductCreateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, CreateView):
    """Create a new product."""

    template_name = "dashboard/admin/products/product-create.html"
    queryset = Product.objects.all()
    form_class = ProductForm
    success_message = "Product created successfully. You can now edit its details."

    def form_valid(self, form):
        form.instance.user = self.request.user
        super().form_valid(form)
        return redirect(reverse_lazy("dashboard:admin:product-edit", kwargs={"pk": form.instance.pk}))

    def get_success_url(self):
        return reverse_lazy("dashboard:admin:products-list")


class AdminProductsListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    """Paginated, filterable product listing for admins."""

    template_name = "dashboard/admin/products/products-list.html"
    paginate_by = 25

    def get_paginate_by(self, queryset):
        return self.request.GET.get("page_size", self.paginate_by)

    def get_queryset(self):
        queryset = Product.objects.all()
        if search_q := self.request.GET.get("q"):
            queryset = queryset.filter(title__icontains=search_q)
        if category_id := self.request.GET.get("category_id"):
            queryset = queryset.filter(category__id=category_id)
        if brand_id := self.request.GET.get("brand_id"):
            queryset = queryset.filter(brand__id=brand_id)

        if order_by := self.request.GET.get("order_by"):
            if order_by in ALLOWED_ORDER_FIELDS:
                queryset = queryset.order_by(order_by)

        if price_range := self.request.GET.get("price_range"):
            try:
                min_price, max_price = price_range.split("-")
                queryset = queryset.filter(price__gte=min_price, price__lte=max_price)
            except ValueError:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_items"] = self.get_queryset().count()
        context["brands"] = Brand.objects.annotate(
            product_count=Count(
                "product",
                filter=Q(product__status=ProductStatus.publish.value),
            )
        )
        context["categories"] = (
            Category.objects.annotate(
                product_count=Count(
                    "product",
                    filter=Q(product__status=ProductStatus.publish.value),
                )
            ).filter(product_count__gt=0)
        )
        context["view_mode"] = self.request.GET.get("view", "grid")

        active_filters = []
        if q := self.request.GET.get("q"):
            active_filters.append({"label": f"Search : {q}", "param": "q"})

        if category_id := self.request.GET.get("category_id"):
            try:
                cat = Category.objects.get(id=category_id)
                active_filters.append({"label": f"Category : {cat.title}", "param": "category_id"})
            except Category.DoesNotExist:
                pass

        if price_range := self.request.GET.get("price_range"):
            active_filters.append({
                "label": f"Price Range : ${price_range.replace('-', ' to $')}",
                "param": "price_range",
            })

        if order_by := self.request.GET.get("order_by"):
            if order_by == "price":
                label = "Price Low to High"
            elif order_by == "-price":
                label = "Price High to Low"
            else:
                label = "Sorted"
            active_filters.append({"label": label, "param": "order_by"})

        if brand_id := self.request.GET.get("brand_id"):
            try:
                brand = Brand.objects.get(id=brand_id)
                active_filters.append({"label": f"Brand : {brand.name}", "param": "brand_id"})
            except Brand.DoesNotExist:
                pass

        context["active_filters"] = active_filters
        context["has_filters"] = bool(active_filters)
        return context


class AdminProductEditView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, UpdateView):
    """Edit an existing product."""

    template_name = "dashboard/admin/products/product-edit.html"
    queryset = Product.objects.all()
    form_class = ProductForm
    success_message = "The product has been updated successfully."

    def get_success_url(self):
        return reverse_lazy("dashboard:admin:product-edit", kwargs={"pk": self.get_object().pk})


@staff_member_required
@require_POST
def AdminProductDeleteView(request, pk):
    """Delete a product (staff-only, POST-only)."""
    product = get_object_or_404(Product, pk=pk)
    title = product.title
    product.delete()
    messages.success(request, f'"{title}" was deleted successfully.')
    return redirect("dashboard:admin:products-list")


@staff_member_required
@require_POST
def AdminBrandQuickCreateView(request):
    """Quickly create a new brand via AJAX (staff-only, POST-only)."""
    name = request.POST.get("name", "").strip()
    if not name:
        return JsonResponse({"error": "Name is required."}, status=400)
    if Brand.objects.filter(name__iexact=name).exists():
        return JsonResponse({"error": "This brand already exists."}, status=400)
    brand = Brand.objects.create(name=name)
    return JsonResponse({"id": brand.pk, "name": brand.name})


@staff_member_required
@require_POST
def AdminCategoryQuickCreateView(request):
    """Quickly create a new category via AJAX (staff-only, POST-only)."""
    title = request.POST.get("title", "").strip()
    if not title:
        return JsonResponse({"error": "Title is required."}, status=400)
    if Category.objects.filter(title__iexact=title).exists():
        return JsonResponse({"error": "This category already exists."}, status=400)
    category = Category.objects.create(title=title)
    return JsonResponse({"id": category.pk, "title": category.title})


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

class AdminDashboardOrdersListView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, ListView):
    """Paginated, filterable order listing for admins."""

    template_name = "dashboard/admin/orders/orders-list.html"
    paginate_by = 5

    def get_paginate_by(self, queryset):
        return self.request.GET.get("page_size", self.paginate_by)

    def get_queryset(self):
        queryset = OrderModel.objects.all()
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
            if order_by in {"created_date", "-created_date", "total_price", "-total_price", "status", "-status"}:
                queryset = queryset.order_by(order_by)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_items"] = self.get_queryset().count()
        return context


class AdminOrderDetailView(LoginRequiredMixin, HasAdminAccessPermission, DetailView):
    """Detailed view of a single order for admins."""

    template_name = "dashboard/admin/orders/order-detail.html"

    def get_queryset(self):
        return OrderModel.objects.all()


class AdminOrderInvoiceDetailView(LoginRequiredMixin, HasAdminAccessPermission, DetailView):
    """Invoice view for a successful order."""

    template_name = "dashboard/admin/orders/order-invoice.html"

    def get_queryset(self):
        return OrderModel.objects.filter(status=OrderStatusType.success.value)


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

# Allowed fields for the ``?order_by=`` query parameter (customers).
ALLOWED_CUSTOMER_ORDER_FIELDS = {"created_date", "-created_date", "email", "-email"}


class AdminCustomersListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    """Paginated, searchable, filterable customer listing for admins."""

    template_name = "dashboard/admin/customers/customers-list.html"
    paginate_by = 20

    def get_paginate_by(self, queryset):
        return self.request.GET.get("page_size", self.paginate_by)

    def get_queryset(self):
        queryset = User.objects.exclude(type=UserType.superuser.value)
        if search_q := self.request.GET.get("q"):
            queryset = queryset.filter(
                Q(email__icontains=search_q)
                | Q(user_profile__first_name__icontains=search_q)
                | Q(user_profile__last_name__icontains=search_q)
                | Q(user_profile__phone_number__icontains=search_q)
            )
        if verified := self.request.GET.get("verified"):
            if verified == "1":
                queryset = queryset.filter(is_verified=True)
            elif verified == "0":
                queryset = queryset.filter(is_verified=False)
        if is_active := self.request.GET.get("is_active"):
            if is_active == "1":
                queryset = queryset.filter(is_active=True)
            elif is_active == "0":
                queryset = queryset.filter(is_active=False)
        if user_type := self.request.GET.get("type"):
            if user_type in {"1", "2"}:
                queryset = queryset.filter(type=int(user_type))
        if order_by := self.request.GET.get("order_by"):
            if order_by in ALLOWED_CUSTOMER_ORDER_FIELDS:
                queryset = queryset.order_by(order_by)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_items"] = self.get_queryset().count()
        return context


class AdminCustomerDetailView(LoginRequiredMixin, HasAdminAccessPermission, DetailView):
    """Detailed view of a single customer for admins."""

    template_name = "dashboard/admin/customers/customer-detail.html"

    def get_queryset(self):
        return User.objects.exclude(type=UserType.superuser.value)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_object()
        context["orders"] = OrderModel.objects.filter(user=customer)
        context["orders_count"] = context["orders"].count()
        context["orders_success"] = context["orders"].filter(
            status=OrderStatusType.success.value
        ).count()
        context["reviews_count"] = ReviewModel.objects.filter(user=customer).count()
        context["wishlist_count"] = customer.wishlistmodel_set.count()
        context["addresses_count"] = customer.useraddressmodel_set.count()
        return context


class AdminCustomerEditView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, UpdateView):
    """Edit customer account settings: status, role, and profile info."""

    template_name = "dashboard/admin/customers/customer-edit.html"
    form_class = CustomerEditForm
    success_message = "Customer updated successfully."

    def get_queryset(self):
        return User.objects.exclude(type=UserType.superuser.value)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # CustomerEditForm is not a ModelForm, so remove 'instance'
        kwargs.pop("instance", None)
        kwargs["user"] = self.get_object()
        return kwargs

    def form_valid(self, form):
        customer = self.get_object()
        data = form.cleaned_data

        # Update User model fields
        customer.is_active = data["is_active"]
        customer.is_verified = data["is_verified"]
        new_type = data["type"]

        # Update is_staff flag when promoting to admin
        customer.type = new_type
        customer.is_staff = (new_type == UserType.admin.value)
        customer.save(update_fields=["is_active", "is_verified", "type", "is_staff"])

        # Update Profile model fields
        profile = customer.user_profile
        profile.first_name = data["first_name"]
        profile.last_name = data["last_name"]
        profile.phone_number = data["phone_number"]
        profile.save(update_fields=["first_name", "last_name", "phone_number"])

        logger.info(
            "Customer #%s updated by admin %s (active=%s, verified=%s, type=%s)",
            customer.pk, self.request.user.email,
            customer.is_active, customer.is_verified, customer.get_type_display(),
        )
        messages.success(self.request, self.success_message)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("dashboard:admin:customer-detail", kwargs={"pk": self.kwargs["pk"]})


@staff_member_required
@require_POST
def AdminCustomerToggleActiveView(request, pk):
    """Toggle a customer's active status (AJAX, staff-only, POST-only)."""
    customer = get_object_or_404(User.objects.exclude(type=UserType.superuser.value), pk=pk)
    customer.is_active = not customer.is_active
    customer.save(update_fields=["is_active"])
    logger.info(
        "Customer #%s active status toggled to %s by %s",
        pk, customer.is_active, request.user.email,
    )
    return JsonResponse({"is_active": customer.is_active})


@staff_member_required
@require_POST
def AdminCustomerToggleVerifiedView(request, pk):
    """Toggle a customer's email verified status (AJAX, staff-only, POST-only)."""
    customer = get_object_or_404(User.objects.exclude(type=UserType.superuser.value), pk=pk)
    customer.is_verified = not customer.is_verified
    customer.save(update_fields=["is_verified"])
    logger.info(
        "Customer #%s verified status toggled to %s by %s",
        pk, customer.is_verified, request.user.email,
    )
    return JsonResponse({"is_verified": customer.is_verified})


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

class AdminReviewListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    """Paginated, filterable review listing for admins."""

    template_name = "dashboard/admin/reviews/review-list.html"
    paginate_by = 10

    def get_paginate_by(self, queryset):
        return self.request.GET.get("page_size", self.paginate_by)

    def get_queryset(self):
        queryset = ReviewModel.objects.all()
        if search_q := self.request.GET.get("q"):
            queryset = queryset.filter(product__title__icontains=search_q)
        if status := self.request.GET.get("status"):
            queryset = queryset.filter(status=status)
        if order_by := self.request.GET.get("order_by"):
            if order_by in {"created_date", "-created_date", "rate", "-rate", "status", "-status"}:
                queryset = queryset.order_by(order_by)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_items"] = self.get_queryset().count()
        return context


class AdminReviewEditView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, UpdateView):
    """Edit/moderate a review (change status, etc.)."""

    template_name = "dashboard/admin/reviews/review-edit.html"
    queryset = ReviewModel.objects.all()
    form_class = ReviewForm
    success_message = "Changes saved successfully."

    def get_success_url(self) -> str:
        return reverse_lazy("dashboard:admin:review-list")


# ---------------------------------------------------------------------------
# Coupons
# ---------------------------------------------------------------------------

class AdminCouponListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    """Paginated list of discount coupons."""

    template_name = "dashboard/admin/coupons/coupon-list.html"
    paginate_by = 10

    def get_queryset(self):
        queryset = CouponModel.objects.all().order_by("-created_date")
        if search_q := self.request.GET.get("q"):
            queryset = queryset.filter(code__icontains=search_q)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_items"] = self.get_queryset().count()
        return context


class AdminCouponCreateView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, CreateView):
    """Create a new discount coupon."""

    template_name = "dashboard/admin/coupons/coupon-create.html"
    form_class = CouponForm
    success_url = reverse_lazy("dashboard:admin:coupon-list")
    success_message = "Coupon created successfully."


class AdminCouponEditView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, UpdateView):
    """Edit an existing coupon."""

    template_name = "dashboard/admin/coupons/coupon-edit.html"
    queryset = CouponModel.objects.all()
    form_class = CouponForm
    success_url = reverse_lazy("dashboard:admin:coupon-list")
    success_message = "Coupon updated successfully."


class AdminCouponDeleteView(LoginRequiredMixin, HasAdminAccessPermission, SuccessMessageMixin, DeleteView):
    """Delete a coupon."""

    template_name = "dashboard/admin/coupons/coupon-delete.html"
    queryset = CouponModel.objects.all()
    success_url = reverse_lazy("dashboard:admin:coupon-list")
    success_message = "Coupon deleted successfully."


# ---------------------------------------------------------------------------
# CSV Exports
# ---------------------------------------------------------------------------

@staff_member_required
def admin_export_orders_csv(request):
    """Export all orders as CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)
    writer.writerow(["Order ID", "Customer", "Email", "Total Price", "Status", "Date", "Address", "City", "State"])
    for order in OrderModel.objects.select_related("user__user_profile").all():
        writer.writerow([
            order.id,
            order.user.user_profile.get_fullname(),
            order.user.email,
            order.total_price,
            OrderStatusType(order.status).label,
            order.created_date.strftime("%Y-%m-%d %H:%M"),
            order.address,
            order.city,
            order.state,
        ])
    return response


@staff_member_required
def admin_export_customers_csv(request):
    """Export all customers as CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="customers.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Email", "Full Name", "Phone", "Role", "Verified", "Active", "Joined"])
    for user in User.objects.exclude(is_superuser=True).select_related("user_profile"):
        writer.writerow([
            user.id,
            user.email,
            user.user_profile.get_fullname(),
            user.user_profile.phone_number or "-",
            UserType(user.type).label,
            "Yes" if user.is_verified else "No",
            "Yes" if user.is_active else "No",
            user.created_date.strftime("%Y-%m-%d %H:%M"),
        ])
    return response


@staff_member_required
def admin_export_products_csv(request):
    """Export all products as CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Title", "Brand", "Price", "Discount %", "Final Price", "Stock", "Status", "Rating", "Created"])
    for product in Product.objects.select_related("brand").all():
        writer.writerow([
            product.id,
            product.title,
            product.brand.name if product.brand else "-",
            product.price,
            product.discount,
            product.get_price(),
            product.stock,
            ProductStatus(product.status).label,
            product.avg_rate,
            product.created_date.strftime("%Y-%m-%d %H:%M"),
        ])
    return response


@staff_member_required
def admin_export_coupons_csv(request):
    """Export all coupons as CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="coupons.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Code", "Discount %", "Max Usage", "Used Count", "Expiration", "Created"])
    for coupon in CouponModel.objects.all():
        writer.writerow([
            coupon.id,
            coupon.code,
            coupon.discount_percent,
            coupon.max_limit_usage,
            coupon.used_by.count(),
            coupon.expiration_date.strftime("%Y-%m-%d %H:%M") if coupon.expiration_date else "-",
            coupon.created_date.strftime("%Y-%m-%d %H:%M"),
        ])
    return response


# ---------------------------------------------------------------------------
# Contact Messages
# ---------------------------------------------------------------------------

class AdminMessagesListView(HasAdminAccessPermission, LoginRequiredMixin, ListView):
    """List all contact form messages with filtering and search."""

    template_name = "dashboard/admin/messages/messages-list.html"
    paginate_by = 20

    VALID_ORDER_FIELDS = {
        "created_date", "-created_date", "name", "-name", "status", "-status"
    }

    def get_queryset(self):
        qs = ContactMessage.objects.all()

        # Search
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(email__icontains=q)
                | Q(subject__icontains=q)
            )

        # Status filter
        status = self.request.GET.get("status", "")
        if status:
            qs = qs.filter(status=status)

        # Ordering
        order_by = self.request.GET.get("order_by", "-created_date")
        if order_by not in self.VALID_ORDER_FIELDS:
            order_by = "-created_date"
        qs = qs.order_by(order_by)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_items"] = self.get_queryset().count()
        context["status_choices"] = ContactStatusType.choices
        return context


class AdminMessageDetailView(HasAdminAccessPermission, LoginRequiredMixin, UpdateView):
    """View and manage a single contact message (change status, add notes)."""

    model = ContactMessage
    fields = ["status", "admin_notes"]
    template_name = "dashboard/admin/messages/message-detail.html"
    success_url = reverse_lazy("dashboard:admin:messages-list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["status"].widget = forms_module.Select(
            attrs={"class": "form-select"},
            choices=ContactStatusType.choices,
        )
        form.fields["admin_notes"].widget = forms_module.Textarea(
            attrs={"class": "form-control", "rows": 4, "placeholder": "Internal notes..."},
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mark as read when viewed for the first time
        msg = self.get_object()
        if msg.status == ContactStatusType.unread:
            msg.status = ContactStatusType.read
            msg.save(update_fields=["status", "updated_date"])
        return context

    def form_valid(self, form):
        messages.success(self.request, "Message updated.")
        return super().form_valid(form)


@staff_member_required
def admin_delete_message(request, pk):
    """Delete a contact message."""
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.delete()
    messages.success(request, f"Message from '{msg.name}' deleted.")
    return redirect("dashboard:admin:messages-list")


@staff_member_required
def admin_export_messages_csv(request):
    """Export all contact messages as CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="contact_messages.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Name", "Email", "Subject", "Message", "Status", "Date"])
    for msg in ContactMessage.objects.all():
        writer.writerow([
            msg.id,
            msg.name,
            msg.email,
            msg.subject,
            msg.message,
            msg.get_status_display(),
            msg.created_date.strftime("%Y-%m-%d %H:%M"),
        ])
    return response