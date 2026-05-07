from django import forms
from accounts.models.profiles import Profile
from order.models import CouponModel
from shop.models import Product
from review.models import ReviewModel


class CouponForm(forms.ModelForm):
    """Form for creating and editing discount coupons."""

    class Meta:
        model = CouponModel
        fields = ["code", "discount_percent", "max_limit_usage", "expiration_date"]
        widgets = {
            "code": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. SUMMER2026"}
            ),
            "discount_percent": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "max": 100, "placeholder": "0"}
            ),
            "max_limit_usage": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "placeholder": "10"}
            ),
            "expiration_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["expiration_date"].input_formats = ["%Y-%m-%dT%H:%M"]


class AdminProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "first_name",
            "last_name",
            "phone_number"
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "id": "firstName"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "id": "lastName"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "id": "phone"}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "image",
            "brand",
            "title",
            "slug",
            "description",
            "stock",
            "price",
            "discount",
            "category",
            "status",
        ]

        widgets = {
            # Product Image
            "image": forms.FileInput(
                attrs={
                    "class": "form-control d-none",
                    "id": "image",
                    "accept": "image/*",
                }
            ),

            # Brand
            "brand": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "brand",
                }
            ),

            # Title
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "id": "title",
                    "placeholder": "Product title",
                }
            ),

            # Slug
            "slug": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "id": "slug",
                    "placeholder": "product-title-slug",
                }
            ),

            # Description
            "description": forms.Textarea(
                attrs={
                    "class": "form-control rounded-top-0",
                    "id": "description",
                    "rows": 6,
                    "placeholder": "Write product description here...",
                }
            ),

            # Stock
            "stock": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "id": "stock",
                    "min": 0,
                    "placeholder": "0",
                }
            ),

            # Price
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "id": "price",
                    "min": 0,
                    "step": "0.01",
                    "placeholder": "0.00",
                }
            ),

            # Discount
            "discount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "id": "discount",
                    "min": 0,
                    "max": 100,
                    "placeholder": "0",
                }
            ),

            # Category
            "category": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "id": "category",
                    "size": 5,
                }
            ),

            # Status (radio)
            "status": forms.RadioSelect(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewModel
        fields = ["description", "rate", "status"]

        widgets = {
            "description": forms.Textarea(
                attrs={
                    "class": "form-control rounded-top-0",
                    "rows": 4,
                    "placeholder": "Write review here...",
                }
            ),
            "rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 5,
                }
            ),
            "status": forms.RadioSelect(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rate"].disabled = True


class CustomerEditForm(forms.Form):
    """Form for admin to manage a customer's account settings and profile.

    Allows changing active/verified status, user role, and profile info.
    Not a ModelForm because it spans two models (User + Profile).
    """

    # --- User fields ---
    is_active = forms.BooleanField(
        required=False,
        label="Active Account",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    is_verified = forms.BooleanField(
        required=False,
        label="Email Verified",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    type = forms.TypedChoiceField(
        coerce=int,
        label="User Role",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    # --- Profile fields ---
    first_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First name"}),
    )
    last_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last name"}),
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "+991234567890"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models.users import UserType

        # Build choices excluding superuser (only superusers can create superusers)
        self.fields["type"].choices = [
            (UserType.customer.value, "Customer"),
            (UserType.admin.value, "Admin"),
        ]

        if user:
            self.initial["is_active"] = user.is_active
            self.initial["is_verified"] = user.is_verified
            self.initial["type"] = user.type
            self.initial["first_name"] = user.user_profile.first_name
            self.initial["last_name"] = user.user_profile.last_name
            self.initial["phone_number"] = user.user_profile.phone_number