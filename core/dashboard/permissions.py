"""Role-based permission mixins for the dashboard."""

from django.contrib.auth.mixins import UserPassesTestMixin

from accounts.models import UserType


class HasCustomerAccessPermission(UserPassesTestMixin):
    """Allow access only to authenticated users with the *customer* role."""

    def test_func(self):
        if self.request.user.is_authenticated:
            return self.request.user.type == UserType.customer.value
        return False


class HasAdminAccessPermission(UserPassesTestMixin):
    """Allow access only to authenticated admin or superuser users."""

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        return (
            user.is_superuser
            or user.type in [UserType.admin.value, UserType.superuser.value]
        )