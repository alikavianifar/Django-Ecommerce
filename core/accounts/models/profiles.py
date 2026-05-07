"""User profile model with automatic creation via signal."""

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models.users import User, UserType
from accounts.validators import validate_phone_number


class Profile(models.Model):
    """Extended profile information for a :model:`accounts.User`."""

    id = models.BigIntegerField(primary_key=True)
    user = models.OneToOneField(
        "User", on_delete=models.CASCADE, related_name="user_profile"
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=15,
        validators=[validate_phone_number],
        help_text="Enter the phone number in international format with country code. Example: +991234567890",
    )
    image = models.ImageField(upload_to="profile/", default="profile/default.png")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def get_fullname(self):
        """Return the user's full name, or 'New Client' if empty."""
        if self.first_name or self.last_name:
            return self.first_name + " " + self.last_name
        return "New Client"


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Automatically create a Profile when a new User is created."""
    if created:
        Profile.objects.create(user=instance, pk=instance.pk)