[فارسی](docs/README.fa.md)

# <div align="center"> Django E-Commerce</div>

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2_LTS-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Stripe](https://img.shields.io/badge/Stripe-Payments-635BFF?logo=stripe&logoColor=white)](https://stripe.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-85_Passed-brightgreen?logo=pytest&logoColor=white)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

<p align="center">
A production-ready, full-featured <strong>e-commerce web application</strong> built with <strong>Django 4.2 LTS</strong>.<br/>
Complete shopping experience from product browsing and cart management to Stripe payment processing with webhook verification.
</p>

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Architecture Overview](#-architecture-overview)
- [Getting Started](#-getting-started)
- [Running Tests](#-running-tests)
- [Project Structure](#-project-structure)
- [Security Practices](#-security-practices)
- [API & URL Endpoints](#-api--url-endpoints)
- [Limitations & Future Work](#-limitations--future-work)
- [License](#-license)

---

## ✨ Key Features

### 🛒 Shopping & Products
- **Product Catalog** — Paginated product listing with search, filtering by category, brand, and price range, and multi-field sorting (price, date, title)
- **Product Detail Page** — Full product info with image gallery, zoom functionality, star ratings, and verified customer reviews
- **Shopping Cart** — Session-based cart for guest users with automatic database synchronisation for authenticated users (via Django signals on login/logout)
- **Wishlist** — Save/remove products to a personal wishlist with toggle functionality (AJAX-powered)
- **Coupon & Discount System** — Percentage-based discount coupons with usage limits, expiration dates, and per-user tracking
- **Tax Calculation** — Automatic 10% tax applied on discounted subtotals with precise `Decimal` arithmetic
- **Fake Data Generator** — Built-in management command (`generate_fake_products`) to create realistic test data with images using Faker

### 💳 Checkout & Payment
- **Stripe Checkout Integration** — Secure redirect to Stripe's hosted checkout page with full session management
- **Stripe Webhook** — Server-side verification of `checkout.session.completed` events with signature validation
- **Order Lifecycle** — Three-state order management: Pending → Success / Failed, with automatic cart clearing on payment
- **Order Cancellation** — Automatic order status update to "Failed" when user cancels at Stripe checkout

### 👤 Authentication & Users
- **Custom User Model** — Email-based authentication (no username), with `customer`, `admin`, and `superuser` roles
- **Email Verification** — Time-limited signed tokens (Django Signer) with configurable expiry (default: 24 hours)
- **Password Reset** — Complete email-based password recovery flow with custom HTML templates
- **Session Cycling** — Session key regenerated on login to prevent session fixation attacks
- **Anti-Enumeration** — Deliberately vague error messages on registration to prevent email discovery

### 📊 Admin Dashboard
- **Analytics Dashboard** — Professional dashboard with KPI cards (revenue, orders, customers, products), Chart.js revenue charts (bar + line combo), and doughnut order status chart
- **Product Management** — Full CRUD for products with image upload, multi-category assignment, brand selection, and publish/draft status
- **Quick Create** — AJAX-powered inline creation of new brands and categories without leaving the product form
- **Order Management** — View all orders with search, status filtering, sorting, and detailed order/invoice views
- **Customer Management** — Full customer list with role/status filters, AJAX toggles for active/verified status, profile editing, and role management (Customer ↔ Admin)
- **Coupon Management** — Full CRUD for discount coupons with code, percentage, usage limits, expiration dates, and live status indicators (Active/Expired/Limit Reached)
- **Review Moderation** — Review listing with status filtering (Pending/Accepted/Rejected), search, and edit capability
- **CSV Export** — One-click CSV export for orders, customers, products, and coupons from any list page and the dashboard
- **Profile Settings** — Edit personal information, profile image, and change password (logs out after password change)

### 👥 Customer Dashboard
- **Personal Dashboard** — Overview with KPI cards (total spent, orders, wishlist, reviews), order status breakdown, and quick links
- **Profile Management** — Edit personal information, profile image, and password
- **Address Book** — Full CRUD for shipping addresses with sorting
- **Order History** — View past orders with search, status filtering, sorting, and invoice download
- **Wishlist Preview** — Recent wishlist items on dashboard with links to product pages
- **Wishlist Management** — Browse and remove wishlist items with search and pagination
- **My Reviews** — View all submitted reviews and their moderation status

### 🛡️ Security Features
- **Rate Limiting** — IP-based rate limiting on login (10/min), registration (5/min), email resend (3/min), and coupon validation (10/min per user)
- **Order-by Whitelist** — All user-sortable fields validated against an explicit whitelist to prevent SQL injection
- **CSRF Protection** — Django's built-in CSRF middleware on all forms
- **XSS Protection** — Django's security middleware with `X-Content-Type-Options`, `X-Frame-Options`
- **Signed Tokens** — Email verification uses Django's cryptographic signer with configurable expiry
- **Input Validation** — Phone number validation (via `phonenumbers` library), password strength validation, form-level sanitisation
- **Environment Variables** — All secrets managed via `.env` files using `python-decouple`

### 🔧 DevOps & Testing
- **Docker Compose** — Three-service setup: Django app, PostgreSQL 15, and smtp4dev (email testing)
- **85 Automated Tests** — Comprehensive test coverage across all 6 apps (models, forms, views, signals, tokens)
- **GitHub Actions CI** — Automated test execution on every push and pull request
- **Structured Logging** — Module-level logging with per-app configuration and verbose formatting
- **Debug Toolbar** — Django Debug Toolbar integrated for development profiling

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10 |
| **Framework** | Django 4.2 LTS |
| **Database** | PostgreSQL 15 (Docker) / SQLite 3 (local development) |
| **Payment** | Stripe Checkout + Webhooks |
| **Authentication** | Django Auth + Custom User Model + Email Verification + Rate Limiting |
| **Frontend** | Django Templates (SSR), Bootstrap 5, Chart.js 4, Swiper.js, AOS.js, GLightbox, Drift Zoom |
| **Email** | smtp4dev (development SMTP server) |
| **Containerisation** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions |
| **Testing** | Django TestCase (85 tests) |
| **Security** | django-ratelimit, python-decouple, phonenumbers |
| **Data** | Faker (test data generation) |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Client (Browser)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼────────────────────────────────────────┐
│                    Django 4.2 (SSR)                             │
│                                                                 │
│  ┌──────────┐ ┌──────┐ ┌──────┐ ┌───────┐ ┌────────┐ ┌────────┐ │
│  │ accounts │ │ shop │ │ cart │ │ order │ │ review │ │website │ │
│  │          │ │      │ │      │ │       │ │        │ │        │ │
│  │• Login   │ │• List│ │• Add │ │• Check│ │• Submit│ │• Home  │ │
│  │• Register│ │• Deta│ │• Rm  │ │• Pay  │ │• Rate  │ │• About │ │
│  │• Verify  │ │• Filt│ │• Qty │ │• Coupo│ │• Moder │ │• Contac│ │
│  │• Reset   │ │• Wish│ │• Sync│ │• Webho│ │• Avg   │ │        │ │
│  └──────────┘ └──────┘ └──────┘ └───────┘ └────────┘ └────────┘ │
│                                                                 │
│  ┌────────────────────────────────────┐                         │
│  │           dashboard                │                         │
│  │  ┌────────────┐ ┌────────────────┐ │                         │
│  │  │   admin    │ │   customer     │ │                         │
│  │  │            │ │                │ │                         │
│  │  │• Products  │ │• Profile       │ │                         │
│  │  │• Orders    │ │• Addresses     │ │                         │
│  │  │• Reviews   │ │• Orders        │ │                         │
│  │  │• Settings  │ │• Wishlist      │ │                         │
│  │  └────────────┘ │• Reviews       │ │                         │
│  │                 └────────────────┘ │                         │
│  └────────────────────────────────────┘                         │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL 15  │  Stripe API  │  smtp4dev  │  Session Store    │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow: Cart → Checkout → Payment

```
Guest adds to cart          ──► Session Storage (cookie-based)
User logs in                ──► Signal syncs DB cart → Session
User modifies cart          ──► Session + DB stay in sync
Checkout                    ──► Order created (status: pending)
Stripe redirect             ──► User pays on Stripe's hosted page
Webhook received            ──► Order marked as "success", cart cleared
User cancels at Stripe      ──► Order marked as "failed"
```

---

## 🚀 Getting Started

### Prerequisites

- **Docker** (recommended) OR **Python 3.10+**
- **Stripe Account** (for payment testing — [test mode keys](https://dashboard.stripe.com/test/apikeys))

### Clone the Repository

```bash
git clone https://github.com/alikavianifar/Django-Ecommerce.git
cd Django-Ecommerce
```

### 🐳 Option 1: Docker (Recommended)

```bash
# 1. Copy environment template and configure
cp envs/dev/django/.env.example envs/dev/django/.env
# Edit .env — set your Stripe test keys

# 2. Build and start all services (Django + PostgreSQL + smtp4dev)
docker-compose up --build

# 3. Run database migrations
docker-compose exec backend sh -c "python manage.py migrate"

# 4. Create a superuser (admin account)
docker-compose exec backend sh -c "python manage.py createsuperuser"

# 5. (Optional) Generate 50 sample products with images
docker-compose exec backend sh -c "python manage.py generate_fake_products --count 50 --use-static-images"
```

| Service | URL |
|---------|-----|
| **Web Application** | http://localhost:8000 |
| **smtp4dev (Email UI)** | http://localhost:5000 |
| **Django Admin** | http://localhost:8000/admin/ |

### 🖥️ Option 2: Local Development (Without Docker)

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp envs/dev/django/.env.example envs/dev/django/.env
# Edit .env — set your SECRET_KEY and Stripe keys

# 4. Apply database migrations
cd core
python manage.py migrate

# 5. Create a superuser
python manage.py createsuperuser

# 6. Start the development server
python manage.py runserver

# 7. (Optional) Generate sample products
python manage.py generate_fake_products --count 50 --use-static-images
```

> **Note:** When running without Docker, the project uses SQLite by default. For PostgreSQL, uncomment the database configuration block in `settings.py`.

---

## 🧪 Running Tests

```bash
cd core

# Run all 85 tests
python manage.py test --verbosity=2

# Run tests for a specific app
python manage.py test accounts --verbosity=2
python manage.py test shop --verbosity=2
python manage.py test cart --verbosity=2
python manage.py test order --verbosity=2
python manage.py test review --verbosity=2
python manage.py test website --verbosity=2
```

### Test Coverage Summary

| App | Tests | What's Tested |
|-----|-------|---------------|
| **accounts** | 23 | User model, profile signal, register/login forms, email verification tokens, auth views |
| **shop** | 18 | Product model (pricing, discount, stars), list/detail views, filters, order-by whitelist, wishlist |
| **cart** | 14 | Session cart (add, remove, update, stock limits, clear, discounts), cart model, AJAX views |
| **order** | 16 | Order/OrderItem models, coupon model, address model, checkout form validation |
| **review** | 11 | Review model, avg_rate signal, form validation, view submission |
| **website** | 3 | Home, About, Contact page loading |
| **Total** | **85** | — |

---

## 📁 Project Structure

```
Ecommerce-Django/
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI pipeline
├── core/                           # Django project root
│   ├── accounts/                   # Custom user model, auth, email verification
│   │   ├── models/
│   │   │   ├── users.py            # Custom User model (email-based)
│   │   │   └── profiles.py         # Profile model (auto-created via signal)
│   │   ├── views.py                # Login, Register, Verify, Resend views
│   │   ├── forms.py                # AuthenticationForm, RegisterForm
│   │   ├── tokens.py               # Signed token generation & verification
│   │   ├── emails.py               # Verification email sender
│   │   ├── validators.py           # Phone number validation
│   │   └── tests.py                # 23 tests
│   ├── shop/                       # Product catalog
│   │   ├── models.py               # Product, Brand, Category, ProductImage, Wishlist
│   │   ├── views.py                # Product list, detail, wishlist toggle
│   │   ├── templatetags/
│   │   │   └── shop_tags.py        # Latest products, similar products, header products
│   │   ├── management/commands/
│   │   │   └── generate_fake_products.py  # Faker-based test data generator
│   │   └── tests.py                # 18 tests
│   ├── cart/                       # Shopping cart
│   │   ├── cart.py                 # CartSession class (session-based cart logic)
│   │   ├── models.py               # CartModel, CartItemModel (DB-backed)
│   │   ├── signals.py              # Login/logout sync signals
│   │   ├── context_processors.py   # Cart available in all templates
│   │   ├── views.py                # Add, remove, update, summary (AJAX)
│   │   └── tests.py                # 14 tests
│   ├── order/                      # Checkout & payment
│   │   ├── models.py               # Order, OrderItem, Coupon, UserAddress
│   │   ├── views.py                # Checkout, Stripe session, webhook, coupon validation
│   │   ├── forms.py                # CheckOutForm (address + coupon validation)
│   │   └── tests.py                # 16 tests
│   ├── dashboard/                  # Role-based dashboards
│   │   ├── admin/                  # Admin: products CRUD, orders, reviews
│   │   │   ├── views.py            # 15 views (list, create, edit, delete, quick-create)
│   │   │   └── forms.py            # ProductForm, ReviewForm, ProfileEditForm
│   │   ├── customer/               # Customer: profile, addresses, orders, wishlist
│   │   │   ├── views.py            # 13 views
│   │   │   └── forms.py            # CustomerProfileEditForm, UserAddressForm
│   │   ├── permissions.py          # HasAdminAccessPermission, HasCustomerAccessPermission
│   │   └── views.py                # Role-based dashboard redirect
│   ├── review/                     # Product reviews
│   │   ├── models.py               # ReviewModel + avg_rate signal
│   │   ├── views.py                # SubmitReviewView (POST-only)
│   │   ├── forms.py                # SubmitReviewForm (product validation)
│   │   └── tests.py                # 11 tests
│   ├── website/                    # Static pages
│   │   ├── views.py                # Home, About, Contact
│   │   └── tests.py                # 3 tests
│   ├── templates/                  # HTML templates (Bootstrap 5)
│   ├── static/                     # CSS, JS, images
│   └── core/                       # Settings, URLs, WSGI
├── dockerfiles/                    # Dockerfile (Python 3.10-slim-buster)
├── envs/
│   └── dev/django/
│       ├── .env.example            # Environment variable template
│       └── .env                    # Your local secrets (git-ignored)
├── docker-compose.yml              # Django + PostgreSQL + smtp4dev
├── requirements.txt                # Pinned Python dependencies
├── LICENSE                         # MIT License
└── README.md
```

---

## 🔒 Security Practices

| Practice | Implementation |
|----------|---------------|
| **No Hardcoded Secrets** | All sensitive values loaded from `.env` via `python-decouple` |
| **`.env` Excluded from Git** | `.gitignore` blocks `*.env`, only `.env.example` is tracked |
| **Rate Limiting** | `django-ratelimit` on login, registration, email resend, coupon validation |
| **CSRF Protection** | Django's `CsrfViewMiddleware` on all forms |
| **XSS Protection** | `SecurityMiddleware` + `X-Frame-Options: DENY` + `X-Content-Type-Options: nosniff` |
| **SQL Injection Prevention** | Order-by fields validated against explicit whitelists |
| **Session Fixation** | `session.cycle_key()` called after every successful login |
| **Email Enumeration** | Registration returns vague messages regardless of email existence |
| **Signed Tokens** | Email verification uses `django.core.signing` with time-limited signatures |
| **Stripe Webhook Security** | Payload signature verified before processing any event |
| **Password Validation** | Django's 4 built-in validators (similarity, minimum length, common passwords, numeric) |
| **Phone Validation** | `phonenumbers` library for international format validation |
| **DEBUG Default** | `DEBUG=False` by default — must be explicitly enabled |

---

## 🌐 API & URL Endpoints

### Public Pages
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Home page |
| GET | `/shop/products/` | Product listing with search & filters |
| GET | `/shop/product-details/<slug>/` | Product detail page |
| GET | `/about/` | About page |
| GET | `/contact/` | Contact page |

### Authentication
| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/accounts/login/` | Login (rate limited: 10/min) |
| GET/POST | `/accounts/register/` | Registration (rate limited: 5/min) |
| GET | `/accounts/logout/` | Logout |
| GET | `/accounts/verify-email/<token>/` | Email verification |
| POST | `/accounts/verify-email/resend/` | Resend verification (rate limited: 3/min) |
| GET/POST | `/accounts/password/reset/` | Password reset flow |

### Cart (AJAX)
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/cart/session/add-product/` | Add product to cart |
| POST | `/cart/session/remove-product/` | Remove product from cart |
| POST | `/cart/session/update-product-quantity/` | Update quantity |
| GET | `/cart/summary/` | Cart summary page |

### Orders & Payment
| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/order/checkout/` | Checkout → Stripe redirect |
| GET | `/order/completed/` | Order completion page |
| POST | `/order/validate-coupon/` | AJAX coupon validation (rate limited: 10/min) |
| POST | `/order/stripe/webhook/` | Stripe webhook endpoint |

### Wishlist (AJAX)
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/shop/add-or-remove-whishlist/` | Toggle wishlist (authenticated) |

### Dashboards
| URL Prefix | Description |
|------------|-------------|
| `/dashboard/admin/` | Admin dashboard (analytics, products, orders, customers, coupons, reviews, settings) |
| `/dashboard/customer/` | Customer dashboard (overview, profile, addresses, orders, wishlist, reviews) |

### Admin Exports
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/dashboard/admin/export/orders/csv/` | Export all orders as CSV |
| GET | `/dashboard/admin/export/customers/csv/` | Export all customers as CSV |
| GET | `/dashboard/admin/export/products/csv/` | Export all products as CSV |
| GET | `/dashboard/admin/export/coupons/csv/` | Export all coupons as CSV |

---

## 🔮 Limitations & Future Work

This project covers a complete e-commerce flow, but there are many areas for improvement and extension:

- 🔒 **Advanced Auth** — 2FA, social login (Google/GitHub), OAuth2
- 🛒 **E-Commerce** — Elasticsearch, persistent cart, product variants, multi-vendor
- 💳 **Payments** — Multiple gateways, e-wallet, refund management
- 🌍 **i18n** — Multi-language, multi-currency support
- ⚡ **Performance** — Redis caching, Celery async tasks, CDN integration
- 🎨 **UI/UX** — PWA, dark mode, accessibility (WCAG)
- 📊 **Analytics** — SEO optimisation, recommendation engine, A/B testing, advanced reporting
- 🐳 **DevOps** — Kubernetes, Nginx + Gunicorn, auto-scaling, monitoring

👉 For the complete detailed list, see [Future Work](docs/future-work.md).

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built by [Ali Kaviani Far](https://github.com/alikavianifar)**

</div>
