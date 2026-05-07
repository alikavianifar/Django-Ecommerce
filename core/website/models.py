"""Models for the website app."""

from django.db import models


class ContactStatusType(models.IntegerChoices):
    """Status choices for contact messages."""

    unread = 1, "Unread"
    read = 2, "Read"
    replied = 3, "Replied"
    archived = 4, "Archived"


class ContactMessage(models.Model):
    """Stores visitor contact‑form submissions."""

    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.IntegerField(
        choices=ContactStatusType.choices,
        default=ContactStatusType.unread,
    )
    admin_notes = models.TextField(blank=True, default="")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_date"]
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} — {self.subject}"
