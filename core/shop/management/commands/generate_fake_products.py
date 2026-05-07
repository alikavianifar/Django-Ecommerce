# docker compose exec backend python manage.py generate_fake_products --count 50 --username ali@gmail.com --use-static-images    
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
import random
import os

from shop.models import Product, Brand, Category, ProductImage, ProductStatus


CLOTHING_BRANDS = [
    "Zara", "H&M", "Nike", "Adidas", "Gucci", "Prada", "Levi's", "Mango", "Puma", "Uniqlo"
]

CATEGORIES = [
    # Men
    "Men Shirts",
    "Men T-Shirts",
    "Men Jeans",
    "Men Jackets",
    "Men Suits",
    "Men Shoes",
    "Men Hoodies & Sweaters",
    "Men Shorts",
    "Men Sportswear",

    # Women
    "Women Dresses",
    "Women Tops & Blouses",
    "Women Skirts",
    "Women Jeans",
    "Women Jackets & Coats",
    "Women Shoes & Heels",
    "Women Sweaters & Hoodies",
    "Women Activewear",
    "Women Handbags",

    # Accessories
    "Watches",
    "Sunglasses",
    "Belts",
    "Scarves",
    "Caps & Hats",
    "Wallets",
    "Jewelry",
    "Backpacks & Bags",
]

PRODUCT_TITLES = [
    # Men
    "Classic Men Shirt",
    "Casual Cotton T-Shirt",
    "Slim Fit Jeans",
    "Leather Jacket",
    "Running Sneakers",
    "Formal Suit",
    "Men Polo Shirt",
    "Denim Jacket",
    "Sports Shorts",
    "Casual Hoodie",
    "Wool Sweater",
    "Men Dress Shoes",
    "Training Tracksuit",

    # Women
    "Elegant Women Dress",
    "Mini Skirt",
    "High Heel Sandals",
    "Leather Handbag",
    "Evening Gown",
    "Casual Blouse",
    "Skinny Jeans",
    "Knit Sweater",
    "Summer Top",
    "Maxi Skirt",
    "Ballet Flats",
    "Denim Dress",

    # Accessories
    "Stylish Wrist Watch",
    "Leather Belt",
    "Designer Sunglasses",
    "Wool Scarf",
    "Silk Tie",
    "Baseball Cap",
    "Leather Wallet",
    "Handmade Necklace",
    "Travel Backpack",
    "Sports Cap",
    "Elegant Earrings",
    "Silver Bracelet",
]

PRODUCT_DESCRIPTIONS = [
    "Made from premium cotton for maximum comfort and durability.",
    "Elegant design with high-quality stitching, suitable for both casual and formal wear.",
    "Lightweight and breathable, perfect for summer days.",
    "Designed with a modern fit that looks stylish and feels comfortable.",
    "Crafted from durable materials to withstand daily use.",
    "Trendy piece that can easily be matched with different outfits.",
    "Soft inner lining for extra comfort and warmth during colder months.",
    "Premium leather material with a sleek finish.",
    "Handcrafted details that add uniqueness and charm.",
    "Fashionable yet practical, great for everyday activities.",
    "Minimalist design with timeless appeal.",
    "Comfortable fit with adjustable closure for versatility.",
    "Perfect balance between style and functionality.",
    "High-end product designed for fashion-forward individuals.",
    "Classic look that never goes out of style.",
    "Eco-friendly materials used for sustainable fashion.",
    "Designed to provide support and flexibility while moving.",
    "Ideal accessory to complete any outfit.",
    "Elegant look that adds sophistication to your wardrobe.",
    "Durable, long-lasting, and resistant to regular washing.",
]


class Command(BaseCommand):
    help = "Generate fake clothing & accessories products (uses static/img/product for images if --use-static-images)"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=50, help="Number of products to create")
        parser.add_argument("--username", type=str, default=None, help="Value for the USERNAME_FIELD (may be email in your custom user)")
        parser.add_argument("--email", type=str, default=None, help="Email of the user to assign products to (shortcut)")
        parser.add_argument("--user-id", type=int, default=None, help="User id to assign products to")
        parser.add_argument("--brands", type=int, default=8, help="Ensure at least N brands exist")
        parser.add_argument("--categories", type=int, default=10, help="Ensure at least N categories exist")
        parser.add_argument("--min-price", type=float, default=10.0)
        parser.add_argument("--max-price", type=float, default=500.0)
        parser.add_argument("--min-stock", type=int, default=1)
        parser.add_argument("--max-stock", type=int, default=100)
        parser.add_argument("--min-images", type=int, default=1)
        parser.add_argument("--max-images", type=int, default=3)
        parser.add_argument("--use-static-images", action="store_true", help="Use images from static/img/product")
        parser.add_argument("--publish-rate", type=int, default=80, help="Percent published (0-100)")

    def handle(self, *args, **options):
        count = options["count"]
        desired_brands = options["brands"]
        desired_categories = options["categories"]
        min_price = options["min_price"]
        max_price = options["max_price"]
        min_stock = options["min_stock"]
        max_stock = options["max_stock"]
        min_images = options["min_images"]
        max_images = options["max_images"]
        use_images = options["use_static_images"]
        publish_rate = max(0, min(100, options["publish_rate"]))

        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        User = get_user_model()
        username_field = getattr(User, "USERNAME_FIELD", "username")

        # --- find user ---
        user = None
        if options["user_id"]:
            try:
                user = User.objects.get(id=options["user_id"])
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User id {options['user_id']} not found"))
                return
        elif options["username"]:
            try:
                user = User.objects.get(**{username_field: options["username"]})
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with {username_field}='{options['username']}' not found"))
                return
        elif options["email"]:
            try:
                user = User.objects.get(email=options["email"])
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with email '{options['email']}' not found"))
                return
        else:
            user = User.objects.filter(is_active=True).first()
            if not user:
                self.stdout.write(self.style.ERROR("No active user found. Please create a user first."))
                return

        # --- static images ---
        image_paths = []
        if use_images:
            static_dir = Path(settings.BASE_DIR) / "static" / "img" / "product"
            if static_dir.exists() and static_dir.is_dir():
                image_paths = [p for p in static_dir.iterdir() if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
            if not image_paths:
                self.stdout.write(self.style.WARNING(f"No images found in {static_dir}. Continuing without images."))

        # --- ensure brands ---
        brands = list(Brand.objects.all())
        while len(brands) < desired_brands:
            name = random.choice(CLOTHING_BRANDS)
            slug = slugify(f"{name}-{str(uuid4())[:6]}")
            b = Brand.objects.create(name=name, slug=slug)
            brands.append(b)

        # --- ensure categories ---
        categories = list(Category.objects.all())
        while len(categories) < desired_categories:
            title = random.choice(CATEGORIES)
            slug = slugify(f"{title}-{str(uuid4())[:6]}")
            c = Category.objects.create(title=title, slug=slug)
            categories.append(c)

        created = 0
        for i in range(count):
            title = random.choice(PRODUCT_TITLES)
            base_slug = slugify(title) or f"product-{str(uuid4())[:6]}"
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            price = Decimal(str(round(random.uniform(min_price, max_price), 2)))
            discount = random.choice([0, 5, 10, 15, 20, 25, 30])
            stock = random.randint(min_stock, max_stock)
            brand = random.choice(brands) if brands else None
            status = ProductStatus.publish.value if random.randint(1, 100) <= publish_rate else ProductStatus.draft.value

            product = Product(
                user=user,
                brand=brand,
                title=title,
                slug=slug,
                description=random.choice(PRODUCT_DESCRIPTIONS),
                stock=stock,
                price=price,
                discount=discount,
                status=status
            )
            product.save()

            # add categories
            k = random.randint(1, min(3, len(categories)))
            product.category.add(*random.sample(categories, k))

            # images
            if image_paths:
                main_path = random.choice(image_paths)
                with open(main_path, "rb") as f:
                    fname = f"{slug}-main{main_path.suffix}"
                    product.image.save(fname, File(f), save=True)

                extra_count = random.randint(min_images, max_images)
                for j in range(extra_count):
                    extra_path = random.choice(image_paths)
                    with open(extra_path, "rb") as ef:
                        ef_name = f"{slug}-extra-{j}{extra_path.suffix}"
                        pi = ProductImage(product=product, order=j+1)
                        pi.file.save(ef_name, File(ef), save=True)

            created += 1
            if created % 10 == 0 or created == count:
                self.stdout.write(f"Created {created}/{count} products...")

        self.stdout.write(self.style.SUCCESS(f"Done — created {created} products."))