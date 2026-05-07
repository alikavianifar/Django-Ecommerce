"""Dashboard entry-point view that redirects based on user role."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import View

from accounts.models.users import UserType


class DashboardHomeView(LoginRequiredMixin, View):
    """Redirect authenticated users to the appropriate dashboard (customer or admin)."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.type == UserType.customer.value:
                return redirect(reverse_lazy("dashboard:customer:home"))
            if request.user.type in [UserType.admin.value, UserType.superuser.value]:
                return redirect(reverse_lazy("dashboard:admin:home"))
        else:
            return redirect(reverse_lazy("accounts:login"))
        return super().dispatch(request, *args, **kwargs)