from django.contrib import admin
from shop.models import Product, ProductImage, Brand, Category, WishlistModel

class ProductImageInline(admin.StackedInline):  # یا admin.StackedInline
    model = ProductImage
    extra = 1
    fields = ('file', 'order')
    ordering = ('order',)
    can_delete = True
    show_change_link = False

    class Media:
        js = (
            'admin/js/jquery.init.js',
            'custom_admin/multi_upload.js',
        )
        css = {
            'all': ('custom_admin/custom_admin.css',)
        }

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "stock", "price", "discount", "status", "id")
    inlines = [ProductImageInline]

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "id")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "id")

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("file", "product", "id")

@admin.register(WishlistModel)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "id")