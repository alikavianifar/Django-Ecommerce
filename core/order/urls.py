from django.urls import path
from order.views import OrderCheckoutView, OrderCompletedView, ValidateCouponView, StripeWebhookView

app_name = 'order'

urlpatterns = [
    path("checkout/",OrderCheckoutView.as_view(),name="checkout"),
    path("completed/",OrderCompletedView.as_view(),name="completed"),
    path("validate-coupon/",ValidateCouponView.as_view(),name="validate-coupon"),
    path("stripe/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    ]