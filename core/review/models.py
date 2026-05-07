"""Review models with automatic average-rating recalculation."""

from django.db import models
from django.db.models import Avg
from django.db.models.signals import post_save
from django.core.validators import MaxValueValidator, MinValueValidator
from django.dispatch import receiver


class ReviewStatusType(models.IntegerChoices):
    """Moderation status for a review."""

    pending = 1, "Pending"
    accepted = 2, "Accepted"
    rejected = 3, "Rejected"


class ReviewModel(models.Model):
    """A product review submitted by a customer, subject to moderation."""

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    product = models.ForeignKey("shop.Product", on_delete=models.CASCADE)
    description = models.TextField()
    rate = models.IntegerField(
        default=5, validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    status = models.IntegerField(
        choices=ReviewStatusType.choices, default=ReviewStatusType.pending.value
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_date"]

    def __str__(self):
        return f"{self.user} - {self.product.id}"

    def get_status(self):
        """Return a dict with status id, name, and label."""
        return {
            "id": self.status,
            "title": ReviewStatusType(self.status).name,
            "label": ReviewStatusType(self.status).label,
        }


@receiver(post_save, sender=ReviewModel)
def calculate_avg_review(sender, instance, created, **kwargs):
    """Recalculate the product's average rating when a review is accepted."""
    if instance.status == ReviewStatusType.accepted.value:
        product = instance.product
        average_rating = ReviewModel.objects.filter(
            product=product, status=ReviewStatusType.accepted
        ).aggregate(Avg("rate"))["rate__avg"]
        product.avg_rate = round(average_rating, 1)
        product.save()