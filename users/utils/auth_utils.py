from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from users.mongo.user import User
from users.utils.redis_auth import redis_token_manager
from users.utils.jwt_utils import decode_token

def extract_user_from_request(request):
    """Extract user from request using JWT token"""
    # Try to get Authorization header from request.headers first (DRF)
    auth_header = None
    if hasattr(request, 'headers'):
        auth_header = request.headers.get("Authorization")
    
    # If not found, try META (Django)
    if not auth_header and hasattr(request, 'META'):
        auth_header = request.META.get("HTTP_AUTHORIZATION")

    if not auth_header:
        raise AuthenticationFailed("No authorization header")

    try:
        auth_type, token = auth_header.split()
        if auth_type.lower() != "bearer":
            raise AuthenticationFailed("Invalid authorization type")
    except ValueError:
        raise AuthenticationFailed("Invalid authorization header format")

    if not redis_token_manager.validate_token(token):
        raise AuthenticationFailed("Invalid or expired token")

    decoded = decode_token(token)
    if not decoded:
        raise AuthenticationFailed("Invalid token")

    user = User.objects(id=decoded["user_id"]).first()
    if not user:
        raise AuthenticationFailed("User not found")

    return user
