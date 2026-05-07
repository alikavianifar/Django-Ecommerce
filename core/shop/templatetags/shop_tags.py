"""Shop template tags for rendering product widgets."""

from django import template

from shop.models import Product, ProductStatus, WishlistModel

register = template.Library()


@register.inclusion_tag("includes/latest-products.html", takes_context=True)
def show_latest_products(context):
    """Render the 8 most recent published products."""
    request = context.get("request")
    latest_products = (
        Product.objects.filter(status=ProductStatus.publish.value)
        .distinct()
        .order_by("-created_date")[:8]
    )
    wishlist_items = (
        WishlistModel.objects.filter(user=request.user).values_list(
            "product__id", flat=True
        )
        if request.user.is_authenticated
        else []
    )
    return {
        "latest_products": latest_products,
        "request": request,
        "wishlist_items": wishlist_items,
    }


@register.inclusion_tag("includes/similar-products.html", takes_context=True)
def show_similar_products(context, product):
    """Render up to 4 products sharing a category with *product*."""
    request = context.get("request")
    product_categories = product.category.all()
    similar_products = (
        Product.objects.filter(
            status=ProductStatus.publish.value, category__in=product_categories
        )
        .exclude(id=product.id)
        .distinct()
        .order_by("-created_date")[:4]
    )
    wishlist_items = (
        WishlistModel.objects.filter(user=request.user).values_list(
            "product__id", flat=True
        )
        if request.user.is_authenticated
        else []
    )
    return {
        "similar_products": similar_products,
        "request": request,
        "wishlist_items": wishlist_items,
    }


@register.inclusion_tag("includes/header-product.html")
def header_product():
    """Render up to 3 random discounted products for the header."""
    header_product = Product.objects.filter(
        status=ProductStatus.publish.value, discount__gt=0
    ).order_by("?")[:3]
    return {"header_product": header_product}
