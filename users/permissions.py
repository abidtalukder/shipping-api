from rest_framework.permissions import BasePermission
from users.utils.auth_utils import extract_user_from_request

class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        try:
            extract_user_from_request(request)
            return True
        except Exception:
            return False

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        try:
            user = extract_user_from_request(request)
            return user.is_admin
        except Exception:
            return False