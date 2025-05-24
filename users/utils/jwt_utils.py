import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from users.mongo.user import User
from users.utils.redis_auth import redis_token_manager

def generate_token(user_id):
    """Generate a JWT token for a user"""
    user = User.objects(id=user_id).first()
    if not user:
        return None
        
    payload = {
        "user_id": str(user.id),  # Convert ObjectId to string
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.JWT_TTL_DAYS)
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    
    # Store token in Redis
    redis_token_manager.store_token(token, str(user.id))
    
    return token

def decode_token(token):
    """Decode and validate a JWT token"""
    try:
        # First check if token is in Redis
        if not redis_token_manager.validate_token(token):
            return None

        # Then decode and verify JWT
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        return None

def invalidate_token(token):
    """Invalidate a JWT token"""
    return redis_token_manager.invalidate_token(token)

def refresh_token(old_token):
    """Generate a new token and invalidate the old one"""
    try:
        # First validate the old token
        payload = decode_token(old_token)
        if not payload:
            return None
            
        user_id = payload.get("user_id")
        if not user_id:
            return None
            
        # Generate new token
        new_token = generate_token(user_id)
        if not new_token:
            return None

        # Refresh in Redis
        if redis_token_manager.refresh_token(old_token, new_token):
            return new_token
        return None
    except Exception:
        return None
