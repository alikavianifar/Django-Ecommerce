"""URL configuration for the dashboard app (dispatches to admin / customer)."""

from django.urls import path, include

from dashboard.views import DashboardHomeView

app_name = "dashboard"

urlpatterns = [
    path("home/", DashboardHomeView.as_view(), name="home"),
    path("admin/", include("dashboard.admin.urls")),
    path("customer/", include("dashboard.customer.urls")),
]