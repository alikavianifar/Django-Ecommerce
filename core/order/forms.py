"""Checkout form with address and coupon validation."""

from django import forms
from django.utils import timezone

from order.models import CouponModel, UserAddressModel


class CheckOutForm(forms.Form):
    """Form for the checkout page: validates address ownership and coupon eligibility."""

    address_id = forms.IntegerField(required=True)
    coupon = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(CheckOutForm, self).__init__(*args, **kwargs)

    def clean_address_id(self):
        """Ensure the address belongs to the authenticated user."""
        address_id = self.cleaned_data.get("address_id")
        user = self.request.user
        try:
            address = UserAddressModel.objects.get(id=address_id, user=user)
        except UserAddressModel.DoesNotExist:
            raise forms.ValidationError("Invalid address for the requested user.")
        return address

    def clean_coupon(self):
        """Validate the coupon code: existence, usage limit, expiration, and uniqueness."""
        code = self.cleaned_data.get("coupon")
        if code == "":
            return None

        user = self.request.user
        try:
            coupon = CouponModel.objects.get(code=code)
        except CouponModel.DoesNotExist:
            raise forms.ValidationError("The coupon code is incorrect")

        if coupon.used_by.count() >= coupon.max_limit_usage:
            raise forms.ValidationError("Limitation on the number of uses")

        if coupon.expiration_date and coupon.expiration_date < timezone.now():
            raise forms.ValidationError("Coupon code has expired")

        if user in coupon.used_by.all():
            raise forms.ValidationError("This coupon code has already been used by you")

        return coupon