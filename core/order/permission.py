"""Permission mixin restricting access to customer-type users."""

from django.contrib.auth.mixins import UserPassesTestMixin

from accounts.models import UserType


class HasCustomerAccessPermission(UserPassesTestMixin):
    """Allow access only to authenticated users with the *customer* role."""

    def test_func(self):
        if self.request.user.is_authenticated:
            return self.request.user.type == UserType.customer.value
        return False