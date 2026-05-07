"""Views for the public-facing shop: product listing, detail, and wishlist."""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, View

from review.models import ReviewModel, ReviewStatusType
from shop.models import (
    Brand,
    Category,
    Product,
    ProductStatus,
    WishlistModel,
)

logger = logging.getLogger(__name__)

# Allowed fields for the ``?order_by=`` query parameter.
ALLOWED_ORDER_FIELDS = {"price", "-price", "created_date", "-created_date", "title", "-title"}


class ShopProductListView(ListView):
    """Paginated, filterable product listing for the storefront."""

    template_name = "shop/products.html"
    paginate_by = 6

    def get_paginate_by(self, queryset):
        return self.request.GET.get("page_size", self.paginate_by)

    def get_queryset(self):
        queryset = Product.objects.filter(status=ProductStatus.publish.value)

        if search_q := self.request.GET.get("q"):
            queryset = queryset.filter(title__icontains=search_q)
        if category_id := self.request.GET.get("category_id"):
            queryset = queryset.filter(category__id=category_id)
        if brand_id := self.request.GET.get("brand_id"):
            queryset = queryset.filter(brand__id=brand_id)
        if min_price := self.request.GET.get("min_price"):
            queryset = queryset.filter(price__gte=min_price)
        if max_price := self.request.GET.get("max_price"):
            queryset = queryset.filter(price__lte=max_price)

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
        context["wishlist_items"] = (
            WishlistModel.objects.filter(user=self.request.user).values_list(
                "product__id", flat=True
            )
            if self.request.user.is_authenticated
            else []
        )

        active_filters = []
        if q := self.request.GET.get("q"):
            active_filters.append({"label": f"Search : {q}", "param": "q"})

        if category_id := self.request.GET.get("category_id"):
            try:
                cat = Category.objects.get(id=category_id)
                active_filters.append({"label": f"Category : {cat.title}", "param": "category_id"})
            except Category.DoesNotExist:
                pass

        if min_price := self.request.GET.get("min_price"):
            active_filters.append({"label": f"Min Price: ${min_price}", "param": "min_price"})

        if max_price := self.request.GET.get("max_price"):
            active_filters.append({"label": f"Max Price: ${max_price}", "param": "max_price"})

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


class ShopProductDetailsView(DetailView):
    """Product detail page with reviews and star ratings."""

    template_name = "shop/product-details.html"
    queryset = Product.objects.filter(status=ProductStatus.publish.value)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context["is_wished"] = (
            WishlistModel.objects.filter(user=self.request.user).values_list(
                "product__id", flat=True
            )
            if self.request.user.is_authenticated
            else []
        )
        reviews = ReviewModel.objects.filter(
            product=product, status=ReviewStatusType.accepted.value
        )
        context["reviews"] = reviews
        total_reviews_count = reviews.count()
        context["reviews_count"] = {
            f"rate_{rate}": reviews.filter(rate=rate).count() for rate in range(1, 6)
        }

        if total_reviews_count != 0:
            context["reviews_avg"] = {
                f"rate_{rate}": round(
                    (reviews.filter(rate=rate).count() / total_reviews_count) * 100, 2
                )
                for rate in range(1, 6)
            }
        else:
            context["reviews_avg"] = {f"rate_{rate}": 0 for rate in range(1, 6)}

        return context


class AddOrRemoveWishlistView(LoginRequiredMixin, View):
    """Toggle a product in the authenticated user's wishlist via AJAX POST."""

    def post(self, request, *args, **kwargs):
        product_id = request.POST.get("product_id")

        if product_id:
            try:
                wishlist_item = WishlistModel.objects.get(
                    user=request.user, product__id=product_id
                )
                wishlist_item.delete()
            except WishlistModel.DoesNotExist:
                WishlistModel.objects.create(user=request.user, product_id=product_id)

        return JsonResponse({})