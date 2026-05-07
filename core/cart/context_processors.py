"""Template context processor that injects the cart into every template."""

from .cart import CartSession


def cart_processor(request):
    """Add the current session cart instance to the template context."""
    cart = CartSession(request.session)
    return {"cart": cart}