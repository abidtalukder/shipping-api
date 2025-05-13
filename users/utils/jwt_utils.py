from datetime import datetime, timedelta
import jwt
import os
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from users.mongo.user import User

SECRET_KEY = os.environ.get("SECRET_KEY", "default-fallback")

def generate_token(user_id):
    """
    Generate a JWT token for the user.

    Args:
        user_id (str): The ID of the user.

    Returns:
        str: The generated JWT token.
    """
    payload = {
        "user_id": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token(token):
    """
    Decode a JWT token.
    Args:
        token (str): The JWT token to decode.
    Returns:
        dict: The decoded payload if the token is valid, None otherwise.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
