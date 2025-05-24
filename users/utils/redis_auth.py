import redis
from django.conf import settings
import jwt
from datetime import datetime, timedelta

class RedisTokenManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB
        )

    def store_token(self, token, user_id):
        """Store a token in Redis with user_id"""
        try:
            decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
            exp = decoded.get("exp")
            if exp:
                ttl = exp - int(datetime.now().timestamp())
                if ttl > 0:
                    # Store token with user_id
                    token_key = f"token:{token}"
                    # Ensure user_id is a string
                    if not isinstance(user_id, str):
                        user_id = str(user_id)
                    self.redis_client.setex(token_key, ttl, user_id)
                    print(f"Stored token {token_key} with TTL {ttl}")
                    return True
            return False
        except jwt.InvalidTokenError:
            print(f"Invalid token: {token}")
            return False
        except Exception as e:
            print(f"Error storing token: {str(e)}")
            return False

    def validate_token(self, token):
        """Validate if a token exists in Redis"""
        try:
            # First check if token exists in Redis
            token_key = f"token:{token}"
            exists = self.redis_client.exists(token_key)
            if not exists:
                print(f"Token {token_key} not found in Redis")
                return False

            # Get the user_id associated with the token
            user_id = self.redis_client.get(token_key)
            if not user_id:
                print(f"No user_id found for token {token_key}")
                return False

            # Then verify JWT is still valid
            try:
                decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
                exp = decoded.get("exp")
                if exp and exp > datetime.now().timestamp():
                    print(f"Token {token_key} is valid")
                    return True
                print(f"Token {token_key} is expired")
            except jwt.InvalidTokenError as e:
                print(f"JWT validation error: {str(e)}")
                return False
            
            # If JWT is expired, remove from Redis
            self.invalidate_token(token)
            return False
        except Exception as e:
            print(f"Error validating token: {str(e)}")
            return False

    def refresh_token(self, old_token, new_token):
        """Replace old token with new token in Redis"""
        try:
            # Get user_id from old token
            old_token_key = f"token:{old_token}"
            user_id = self.redis_client.get(old_token_key)
            if not user_id:
                print(f"Old token not found: {old_token}")
                return False

            # Decode user_id from bytes to string if needed
            if isinstance(user_id, bytes):
                user_id = user_id.decode('utf-8')
            if not isinstance(user_id, str):
                user_id = str(user_id)

            # Store new token with the same TTL as the old token
            decoded = jwt.decode(new_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
            exp = decoded.get("exp")
            now = int(datetime.now().timestamp())
            if exp:
                ttl = exp - now
                print(f"Calculated TTL for new token: {ttl}")
                if ttl <= 0:
                    print("TTL is not positive, using fallback TTL of 86400 seconds (1 day)")
                    ttl = 86400
                # Store new token first
                new_token_key = f"token:{new_token}"
                result = self.redis_client.setex(new_token_key, ttl, user_id)
                print(f"Stored new token {new_token_key} with TTL {ttl}, result: {result}")
                # Only invalidate old token after new one is stored
                self.invalidate_token(old_token)
                # Verify the new token was stored
                if self.redis_client.exists(new_token_key):
                    print(f"Verified new token {new_token_key} exists in Redis")
                    return True
                print(f"Failed to verify new token {new_token_key} in Redis")
            else:
                print("No exp in new token JWT payload")
            return False
        except Exception as e:
            print(f"Error refreshing token: {str(e)}")
            return False

    def invalidate_token(self, token):
        """Remove a token from Redis"""
        try:
            self.redis_client.delete(f"token:{token}")
            return True
        except Exception:
            return False

redis_token_manager = RedisTokenManager() 