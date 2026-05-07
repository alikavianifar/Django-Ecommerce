"""
Cart synchronisation signals.

Automatically sync the session cart with the database cart when a user
logs in or logs out.
"""

import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from cart.cart import CartSession

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def post_login(sender, user, request, **kwargs):
    """Merge the DB cart into the session cart after login."""
    cart = CartSession(request.session)
    cart.sync_cart_items_from_db(user)
    logger.debug("Cart synced from DB for user %s on login", user.email)


@receiver(user_logged_out)
def post_logout(sender, user, request, **kwargs):
    """Persist the session cart to the DB before logout."""
    cart = CartSession(request.session)
    cart.merge_session_cart_in_db(user)
    logger.debug("Cart merged to DB for user %s on logout", user.email)