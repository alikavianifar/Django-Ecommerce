"""Order processing views: checkout, payment, coupon validation, Stripe webhook."""

import logging
from decimal import Decimal, ROUND_HALF_UP

import stripe
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView, View
from django_ratelimit.decorators import ratelimit

from cart.cart import CartSession
from cart.models import CartItemModel, CartModel
from order.forms import CheckOutForm
from order.models import CouponModel, OrderItemModel, OrderModel, OrderStatusType, UserAddressModel
from order.permission import HasCustomerAccessPermission

logger = logging.getLogger(__name__)


class OrderCheckoutView(LoginRequiredMixin, HasCustomerAccessPermission, FormView):
    """Checkout page: validates address/coupon, creates order, redirects to Stripe."""

    template_name = "order/checkout.html"
    form_class = CheckOutForm
    success_url = reverse_lazy("order:completed")

    def get_form_kwargs(self):
        kwargs = super(OrderCheckoutView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        canceled = request.GET.get("canceled")
        order_id = request.GET.get("order_id")

        if canceled == "1" and order_id:
            order = OrderModel.objects.filter(id=order_id, user=request.user).first()
            if order and order.status == OrderStatusType.pending.value:
                order.status = OrderStatusType.failed.value
                order.save(update_fields=["status"])
                logger.info("Order #%s cancelled by user %s", order_id, request.user.email)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.request.user

        pending_qs = OrderModel.objects.filter(user=user, status=OrderStatusType.pending.value)
        if pending_qs.exists():
            pending_qs.update(status=OrderStatusType.failed.value)

        cleaned_data = form.cleaned_data
        address = cleaned_data["address_id"]
        coupon = cleaned_data["coupon"]

        cart = CartModel.objects.get(user=user)
        order = self.create_order(address)

        self.create_order_items(order, cart)

        total_price = order.calculate_total_price()
        self.apply_coupon(coupon, order, user, total_price)
        order.save()

        amount_cents = int(
            (order.total_price * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        if amount_cents <= 0:
            return JsonResponse({"message": "Invalid amount"}, status=400)

        stripe.api_key = settings.STRIPE_SECRET_KEY

        success_url = self.request.build_absolute_uri(
            reverse_lazy("order:completed") + f"?order_id={order.id}"
        )
        cancel_url = self.request.build_absolute_uri(
            reverse_lazy("order:checkout") + f"?canceled=1&order_id={order.id}"
        )

        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": settings.STRIPE_CURRENCY,
                    "unit_amount": amount_cents,
                    "product_data": {"name": f"Order #{order.id}"},
                },
                "quantity": 1,
            }],
            metadata={"order_id": str(order.id)},
            success_url=success_url,
            cancel_url=cancel_url,
        )

        order.stripe_session_id = session["id"]
        order.save(update_fields=["stripe_session_id"])
        logger.info("Stripe session %s created for order #%s", session["id"], order.id)

        return redirect(session.url)

    def create_order(self, address):
        """Create a new ``OrderModel`` from the given address."""
        return OrderModel.objects.create(
            user=self.request.user,
            address=address.address,
            state=address.state,
            city=address.city,
            zip_code=address.zip_code,
        )

    def create_order_items(self, order, cart):
        """Populate order items from the user's cart."""
        for item in cart.cart_items.all():
            OrderItemModel.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.get_price(),
            )

    def clear_cart(self, cart):
        """Clear both the DB and session carts."""
        cart.cart_items.all().delete()
        CartSession(self.request.session).clear()

    def apply_coupon(self, coupon, order, user, total_price):
        """Apply an optional coupon discount and calculate tax."""
        subtotal = Decimal(total_price)

        if coupon:
            discount_rate = Decimal(coupon.discount_percent) / Decimal("100")
            subtotal = subtotal - (subtotal * discount_rate)
            subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            order.coupon = coupon

        # Tax is applied on discounted subtotal (10%)
        tax = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        final_price = (subtotal + tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        order.total_price = final_price

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = CartModel.objects.get(user=self.request.user)
        context["addresses"] = UserAddressModel.objects.filter(user=self.request.user)
        total_price = Decimal(cart.calculate_total_price()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_tax = (total_price * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        final_price = (total_price + total_tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        context["total_price"] = total_price
        context["total_tax"] = total_tax
        context["final_price"] = final_price

        cartitem = CartSession(self.request.session)
        cart_items = cartitem.get_cart_items()
        context["cart_items"] = cart_items
        context["total_quantity"] = cartitem.get_total_quantity()
        return context


class OrderCompletedView(LoginRequiredMixin, HasCustomerAccessPermission, TemplateView):
    """Order completion page shown after successful Stripe payment."""

    template_name = "order/completed.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        order_id = self.request.GET.get("order_id")
        order = None

        if order_id:
            order = OrderModel.objects.filter(
                id=order_id, user=self.request.user
            ).first()

        context["order"] = order

        if order and order.status == OrderStatusType.success.value:
            CartSession(self.request.session).clear()
            subtotal = sum(i.price * i.quantity for i in order.order_items.all())
            total = order.total_price
            tax = total - subtotal
            context["subtotal"] = subtotal
            context["tax"] = tax
            context["total"] = total

        return context


class ValidateCouponView(LoginRequiredMixin, HasCustomerAccessPermission, View):
    """AJAX endpoint to validate a coupon code and return updated totals."""

    @method_decorator(ratelimit(key="user", rate="10/m", method="POST", block=True))
    def post(self, request, *args, **kwargs):
        code = request.POST.get("code")
        user = self.request.user

        status_code = 200
        message = "The discount code has been successfully registered"
        total_price = 0
        total_tax = 0
        final_price = 0

        try:
            coupon = CouponModel.objects.get(code=code)
        except CouponModel.DoesNotExist:
            return JsonResponse({"message": "The coupon code is incorrect"}, status=404)
        else:
            if coupon.used_by.count() >= coupon.max_limit_usage:
                status_code, message = 403, "Limitation on the number of uses"

            elif coupon.expiration_date and coupon.expiration_date < timezone.now():
                status_code, message = 403, "Coupon code has expired"

            elif user in coupon.used_by.all():
                status_code, message = 403, "This coupon code has already been used by you"

            else:
                cart = CartModel.objects.get(user=self.request.user)
                total_price = cart.calculate_total_price()
                discount_rate = Decimal(coupon.discount_percent) / Decimal("100")
                total_price = total_price - (total_price * discount_rate)
                total_price = total_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                total_tax = (total_price * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                final_price = (total_price + total_tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return JsonResponse({
            "message": message,
            "total_tax": total_tax,
            "total_price": total_price,
            "final_price": final_price,
        }, status=status_code)


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    """Handle Stripe webhook events (``checkout.session.completed``)."""

    def post(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
        except ValueError:
            return HttpResponseBadRequest("Invalid payload")
        except stripe.error.SignatureVerificationError:
            return HttpResponseBadRequest("Invalid signature")

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]

            session_id = session.get("id")
            payment_intent_id = session.get("payment_intent")
            order_id = session.get("metadata", {}).get("order_id")

            order = None
            if order_id:
                order = OrderModel.objects.filter(id=order_id).first()
            if not order and session_id:
                order = OrderModel.objects.filter(stripe_session_id=session_id).first()

            if order:
                if order.status != OrderStatusType.success.value:
                    order.status = OrderStatusType.success.value
                    order.stripe_payment_intent_id = payment_intent_id
                    order.save(update_fields=["status", "stripe_payment_intent_id"])
                    logger.info("Order #%s marked as successful via Stripe webhook", order.id)

                    if order.coupon:
                        order.coupon.used_by.add(order.user)

                CartItemModel.objects.filter(cart__user=order.user).delete()

        return HttpResponse(status=200)