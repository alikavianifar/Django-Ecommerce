from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.contrib.auth import logout


class DashboardPasswordChange(LoginRequiredMixin, auth_views.PasswordChangeView):
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your password has been updated successfully!")
        logout(self.request)
        return redirect("accounts:login")

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                if field == "__all__":
                    messages.error(self.request, error)
                else:
                    label = form.fields[field].label if field in form.fields else field
                    messages.error(self.request, error)
        return redirect("dashboard:home")