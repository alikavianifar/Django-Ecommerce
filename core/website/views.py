"""Static page views: home, about, and contact."""

import logging

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from website.forms import ContactForm

logger = logging.getLogger(__name__)


class IndexView(TemplateView):
    """Landing / home page."""

    template_name = "website/index.html"


class AboutView(TemplateView):
    """About us page — showcases platform features and tech stack."""

    template_name = "website/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tech_stack"] = [
            {"name": "Django 4.2", "icon": "bi-filetype-py", "color": "#0C4B33"},
            {"name": "PostgreSQL", "icon": "bi-database", "color": "#336791"},
            {"name": "Stripe", "icon": "bi-credit-card", "color": "#635BFF"},
            {"name": "Bootstrap 5", "icon": "bi-bootstrap", "color": "#7952B3"},
            {"name": "Chart.js", "icon": "bi-bar-chart-line", "color": "#FF6384"},
            {"name": "Docker", "icon": "bi-box-seam", "color": "#2496ED"},
            {"name": "Swiper.js", "icon": "bi-images", "color": "#6332F6"},
            {"name": "AOS.js", "icon": "bi-magic", "color": "#3EAAAF"},
            {"name": "Drift.js", "icon": "bi-zoom-in", "color": "#E67E22"},
            {"name": "GLightbox", "icon": "bi-lightbulb", "color": "#F39C12"},
            {"name": "GitHub CI", "icon": "bi-github", "color": "#333333"},
            {"name": "Toastify", "icon": "bi-bell", "color": "#27AE60"},
        ]
        return context


class ContactView(FormView):
    """Contact us page with working form submission."""

    template_name = "website/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("website:contact")

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            "Your message has been sent successfully. We'll get back to you soon!",
        )
        logger.info(
            "New contact message from %s (%s)",
            form.cleaned_data["name"],
            form.cleaned_data["email"],
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "There was an error sending your message. Please check the form.",
        )
        return super().form_invalid(form)