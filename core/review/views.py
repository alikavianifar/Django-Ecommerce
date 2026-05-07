"""Views for submitting product reviews."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from .forms import SubmitReviewForm
from .models import ReviewModel


class SubmitReviewView(LoginRequiredMixin, CreateView):
    """Accept a POST-only review submission from an authenticated user."""

    http_method_names = ["post"]
    model = ReviewModel
    form_class = SubmitReviewForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.save()
        product = form.cleaned_data["product"]
        messages.success(
            self.request,
            "Your comment has been successfully submitted and will be displayed after approval.",
        )
        return redirect(
            reverse_lazy("shop:product-details", kwargs={"slug": product.slug})
        )

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return redirect(self.request.META.get("HTTP_REFERER"))

    def get_queryset(self):
        return ReviewModel.objects.filter(user=self.request.user)