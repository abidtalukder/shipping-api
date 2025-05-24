from rest_framework.permissions import BasePermission
from users.utils.auth_utils import extract_user_from_request
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

class IsAuthenticated(BasePermission):
    """
    Custom permission class to check if user is authenticated.
    """
    message = "Authentication required"

    def has_permission(self, request, view):
        try:
            user = extract_user_from_request(request)
            if not user:
                raise AuthenticationFailed(self.message)
            request.user = user
            return True
        except Exception:
            raise AuthenticationFailed(self.message)

class IsAdminUser(BasePermission):
    """
    Custom permission class to check if user is an admin.
    """
    message = "Authentication required"
    admin_message = "Admin access required"

    def has_permission(self, request, view):
        try:
            user = extract_user_from_request(request)
            if not user:
                raise AuthenticationFailed(self.message)
            request.user = user
            if not user.is_admin:
                raise PermissionDenied(self.admin_message)
            return True
        except AuthenticationFailed as e:
            raise e
        except PermissionDenied as e:
            raise e
        except Exception:
            raise AuthenticationFailed(self.message)