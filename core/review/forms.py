"""Review submission form with product validation."""

from django import forms

from shop.models import Product, ProductStatus
from .models import ReviewModel


class SubmitReviewForm(forms.ModelForm):
    """Form for submitting a review — validates that the product is published."""

    class Meta:
        model = ReviewModel
        fields = ["product", "rate", "description"]
        error_messages = {
            "description": {
                "required": "The description field is required.",
            },
        }

    def clean(self):
        """Verify that the reviewed product exists and is published."""
        cleaned_data = super().clean()
        product = cleaned_data.get("product")

        try:
            Product.objects.get(id=product.id, status=ProductStatus.publish.value)
        except Product.DoesNotExist:
            raise forms.ValidationError("This product does not exist.")

        return cleaned_data