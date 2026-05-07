from django import forms
from accounts.models.profiles import Profile
from order.models import UserAddressModel

class CustomerProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "first_name",
            "last_name",
            "phone_number",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "id": "firstName"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "id": "lastName"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
        }


class UserAddressForm(forms.ModelForm):
        class Meta:
            model = UserAddressModel
            fields = [
                "address",
                "city",
                "state",
                "zip_code",
            ]
            
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            config = {
                "address": {"id": "address", "placeholder": "Street Address"},
                "city": {"id": "city", "placeholder": "City"},
                "state": {"id": "state", "placeholder": "State"},
                "zip_code": {"id": "zip_code", "placeholder": "ZIP Code"},
            }

            for name, attrs in config.items():
                self.fields[name].widget.attrs.update({
                    "class": "form-control",
                    **attrs,
                })