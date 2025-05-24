from django.test import TestCase
import pytest
from .mongo.user import User
from django.test import Client
from rest_framework.test import APIClient
from .utils.jwt_utils import generate_token, decode_token, invalidate_token
from .utils.auth_utils import extract_user_from_request
from .utils.redis_auth import redis_token_manager
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings
import json
import bcrypt
from bson import ObjectId
from datetime import datetime
from deliveries.mongo.delivery import Delivery
import random
import time

# Create your tests here.

@pytest.fixture(autouse=True)
def cleanup_users():
    """Clean up users before each test"""
    User.objects.delete()
    yield
    User.objects.delete()  # Also clean up after each test

@pytest.fixture(autouse=True)
def cleanup_deliveries():
    """Clean up deliveries before each test"""
    Delivery.objects.delete()
    yield
    Delivery.objects.delete()  # Also clean up after each test

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    # Generate a unique username
    timestamp = int(datetime.now().timestamp())
    rand = random.randint(1000, 9999)
    username = f"testuser_{timestamp}_{rand}"
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode(),
        is_admin=False
    )
    user.save()
    yield user
    user.delete()

@pytest.fixture
def sample_admin():
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
        is_admin=True
    )
    admin.save()
    yield admin
    admin.delete()

@pytest.fixture
def auth_headers(sample_user):
    token = generate_token(str(sample_user.id))
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

@pytest.fixture
def admin_auth_headers(sample_admin):
    token = generate_token(str(sample_admin.id))
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

def test_user_creation():
    """Test that a user can be created with valid data"""
    user = User(
        username="newuser",
        email="new@example.com",
        password_hash="hashed_password"
    )
    user.save()
    assert user.username == "newuser"
    assert user.email == "new@example.com"
    assert not user.is_admin
    user.delete()

def test_admin_creation():
    """Test that an admin user can be created"""
    admin = User(
        username="newadmin2",  # Changed to avoid conflict
        email="admin2@example.com",  # Changed to avoid conflict
        password_hash="hashed_password",
        is_admin=True
    )
    admin.save()
    assert admin.username == "newadmin2"
    assert admin.is_admin
    admin.delete()

def test_user_str_representation(sample_user):
    """Test the string representation of a user"""
    assert str(sample_user) == sample_user.username

def test_unique_username(sample_user):
    """Test that usernames must be unique"""
    with pytest.raises(Exception):
        User(
            username=sample_user.username,  # Same as sample_user
            email="different@example.com",
            password_hash="password123"
        ).save()

def test_unique_email(sample_user):
    """Test that emails must be unique"""
    with pytest.raises(Exception):
        User(
            username="different",
            email=sample_user.email,  # Same as sample_user
            password_hash="password123"
        ).save()

def test_invalid_email():
    """Test that invalid emails are rejected"""
    with pytest.raises(Exception):
        User(
            username="testuser",
            email="invalid_email",
            password_hash="password123"
        ).save()

def test_required_fields():
    """Test that required fields are enforced"""
    with pytest.raises(Exception):
        User(username="testuser").save()

def test_register_endpoint(api_client):
    """Test user registration endpoint"""
    data = {
        "username": "newuser2",  # Changed to avoid conflict
        "email": "new2@example.com",  # Changed to avoid conflict
        "password": "password123"
    }
    response = api_client.post("/api/v1/users/register/", data, format="json")
    assert response.status_code == 201

def test_login_success(api_client, sample_user):
    """Test successful login"""
    data = {
        "username": sample_user.username,
        "password": "password123"
    }
    response = api_client.post("/api/v1/users/login/", data, format="json")
    assert response.status_code == 200
    assert "token" in response.data

def test_login_invalid_credentials(api_client, sample_user):
    """Test login with invalid credentials"""
    data = {
        "username": "testuser",
        "password": "wrongpassword"
    }
    response = api_client.post("/api/v1/users/login/", data, format="json")
    assert response.status_code == 401

def test_create_admin_unauthorized(api_client):
    """Test creating admin user without authorization"""
    data = {
        "username": "newadmin3",  # Changed to avoid conflict
        "email": "newadmin3@example.com",  # Changed to avoid conflict
        "password": "admin123"
    }
    response = api_client.post("/api/v1/users/create-admin/", data, format="json")
    assert response.status_code == 401

def test_create_admin_authorized(api_client, admin_auth_headers):
    """Test creating admin user with proper authorization"""
    data = {
        "username": "newadmin4",  # Changed to avoid conflict
        "email": "newadmin4@example.com",  # Changed to avoid conflict
        "password": "admin123"
    }
    response = api_client.post("/api/v1/users/create-admin/", data, format="json", **admin_auth_headers)
    assert response.status_code == 201

def test_logout(api_client, auth_headers):
    """Test logout endpoint"""
    response = api_client.post("/api/v1/users/logout/", **auth_headers)
    assert response.status_code == 200
    # Verify token is invalidated in Redis
    token = auth_headers["HTTP_AUTHORIZATION"].split(" ")[1]
    assert not redis_token_manager.validate_token(token)

def test_token_generation_and_decoding(sample_user):
    """Test JWT token generation and decoding"""
    token = generate_token(str(sample_user.id))
    decoded = decode_token(token)
    assert decoded["user_id"] == str(sample_user.id)

def test_token_invalidation(sample_user):
    """Test token invalidation"""
    token = generate_token(str(sample_user.id))
    redis_token_manager.store_token(token, str(sample_user.id))
    assert redis_token_manager.validate_token(token)
    redis_token_manager.invalidate_token(token)
    assert not redis_token_manager.validate_token(token)

def test_expired_token():
    """Test handling of expired tokens"""
    payload = {
        "user_id": "123",
        "exp": int(datetime.now().timestamp()) - 3600  # 1 hour ago
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    assert decode_token(token) is None

def test_extract_user_success(sample_user, auth_headers):
    """Test successful user extraction from request"""
    request = type("Request", (), {"META": auth_headers})()
    user = extract_user_from_request(request)
    assert user.username == sample_user.username

def test_extract_user_invalid_token():
    """Test user extraction with invalid token"""
    headers = {"HTTP_AUTHORIZATION": "Bearer invalid_token"}
    request = type("Request", (), {"META": headers})()
    with pytest.raises(AuthenticationFailed):
        extract_user_from_request(request)

def test_extract_user_missing_auth():
    """Test user extraction with missing auth header"""
    request = type("Request", (), {"META": {}})()
    with pytest.raises(AuthenticationFailed):
        extract_user_from_request(request)

def test_redis_token_storage(sample_user):
    """Test storing tokens in Redis"""
    token = generate_token(str(sample_user.id))
    assert redis_token_manager.store_token(token, str(sample_user.id))
    assert redis_token_manager.validate_token(token)

def test_redis_token_refresh(sample_user):
    """Test refreshing tokens in Redis"""
    old_token = generate_token(sample_user.id)
    # Ensure a different token by waiting or using a different payload
    time.sleep(1)
    new_token = generate_token(sample_user.id)
    assert old_token != new_token
    # Store old token and verify it exists
    assert redis_token_manager.store_token(old_token, str(sample_user.id))
    assert redis_token_manager.validate_token(old_token)
    # Refresh token
    assert redis_token_manager.refresh_token(old_token, new_token)
    # Verify old token is invalidated
    assert not redis_token_manager.validate_token(old_token)
    # Verify new token exists in Redis
    assert redis_token_manager.redis_client.exists(f"token:{new_token}")
    # Verify new token is valid
    assert redis_token_manager.validate_token(new_token)

def test_redis_token_invalidation(sample_user):
    """Test token invalidation in Redis"""
    token = generate_token(str(sample_user.id))
    redis_token_manager.store_token(token, str(sample_user.id))
    assert redis_token_manager.validate_token(token)
    redis_token_manager.invalidate_token(token)
    assert not redis_token_manager.validate_token(token)
