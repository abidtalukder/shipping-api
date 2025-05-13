from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from users.mongo.user import User
import jwt

def extract_user_from_request(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationFailed("Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token")

    user = User.objects(id=payload["user_id"]).first()
    if not user:
        raise AuthenticationFailed("User not found")
    return user
