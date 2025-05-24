from django.test import TestCase
import pytest
from django.utils import timezone
from .mongo.delivery import Delivery, StatusHistory, VALID_STATUSES
from django.test import Client
from rest_framework.test import APIClient
from users.mongo.user import User
from users.utils.jwt_utils import generate_token
from users.utils.redis_auth import redis_token_manager
import bcrypt
from datetime import datetime, timezone

# Create your tests here.

@pytest.fixture(autouse=True)
def cleanup_data():
    """Clean up users and deliveries before each test"""
    User.objects.delete()
    Delivery.objects.delete()
    yield

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def sample_user():
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode(),
        is_admin=False
    )
    user.save()
    return user

@pytest.fixture
def sample_admin():
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
        is_admin=True
    )
    admin.save()
    return admin

@pytest.fixture
def auth_headers(sample_user):
    token = generate_token(str(sample_user.id))
    redis_token_manager.store_token(token, str(sample_user.id))
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

@pytest.fixture
def admin_auth_headers(sample_admin):
    token = generate_token(str(sample_admin.id))
    redis_token_manager.store_token(token, str(sample_admin.id))
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

@pytest.fixture
def sample_delivery():
    """Create a sample delivery for testing"""
    # Generate a unique delivery ID
    timestamp = int(datetime.now().timestamp())
    delivery_id = f"TEST{timestamp}"
    
    delivery = Delivery(
        delivery_id=delivery_id,
        title="Test Delivery",
        status="pending",
        customer_id="testuser",
        recipient_name="John Doe",
        current_location={
            "type": "Point",
            "coordinates": [-73.935242, 40.730610]
        },
        destination="123 Test St, New York, NY 10001",
        status_history=[
            StatusHistory(
                status="pending",
                location={
                    "type": "Point",
                    "coordinates": [-73.935242, 40.730610]
                }
            )
        ]
    )
    delivery.save()
    yield delivery
    delivery.delete()

@pytest.fixture
def sample_status_history():
    return StatusHistory(
        status="pending",
        location={
            "type": "Point",
            "coordinates": [-73.935242, 40.730610]
        }
    )

def test_delivery_creation():
    """Test delivery creation with valid data"""
    delivery = Delivery(
        delivery_id="TEST123",
        title="Test Delivery",
        status="pending",
        customer_id="testuser",
        recipient_name="John Doe",
        current_location={
            "type": "Point",
            "coordinates": [-73.935242, 40.730610]
        },
        destination="123 Test St, New York, NY 10001"
    )
    delivery.save()
    assert delivery.delivery_id == "TEST123"
    assert delivery.status == "pending"

def test_delivery_to_dict(sample_delivery):
    """Test delivery to dictionary conversion"""
    delivery_dict = sample_delivery.to_dict()
    assert delivery_dict["delivery_id"] == sample_delivery.delivery_id
    assert delivery_dict["status"] == "pending"
    assert delivery_dict["customer_id"] == "testuser"

def test_status_history_creation():
    """Test status history creation"""
    status_history = StatusHistory(
        status="pending",
        location={
            "type": "Point",
            "coordinates": [-73.935242, 40.730610]
        }
    )
    assert status_history.status == "pending"
    assert status_history.location["type"] == "Point"

def test_status_history_to_dict():
    """Test status history to dictionary conversion"""
    status_history = StatusHistory(
        status="pending",
        location={
            "type": "Point",
            "coordinates": [-73.935242, 40.730610]
        }
    )
    history_dict = status_history.to_dict()
    assert history_dict["status"] == "pending"
    assert history_dict["location"]["type"] == "Point"

def test_delivery_status_validation():
    """Test delivery status validation"""
    with pytest.raises(Exception):
        Delivery(
            delivery_id="TEST123",
            title="Test Delivery",
            status="invalid_status",  # Invalid status
            customer_id="testuser",
            recipient_name="John Doe",
            current_location={
                "type": "Point",
                "coordinates": [-73.935242, 40.730610]
            },
            destination="123 Test St, New York, NY 10001"
        ).save()

def test_delivery_title_length():
    """Test delivery title length validation"""
    with pytest.raises(Exception):
        Delivery(
            delivery_id="TEST123",
            title="x" * 101,  # Too long
            status="pending",
            customer_id="testuser",
            recipient_name="John Doe",
            current_location={
                "type": "Point",
                "coordinates": [-73.935242, 40.730610]
            },
            destination="123 Test St, New York, NY 10001"
        ).save()

def test_get_delivery_details(api_client, auth_headers, sample_delivery):
    """Test getting delivery details"""
    response = api_client.get(f"/api/v1/deliveries/{sample_delivery.delivery_id}/", **auth_headers)
    assert response.status_code == 200
    assert response.data["delivery_id"] == sample_delivery.delivery_id

def test_get_nonexistent_delivery(api_client, auth_headers):
    """Test getting a nonexistent delivery"""
    response = api_client.get("/api/v1/deliveries/NONEXISTENT/", **auth_headers)
    assert response.status_code == 404

def test_get_my_deliveries(api_client, auth_headers, sample_delivery):
    """Test getting user's deliveries"""
    response = api_client.get("/api/v1/deliveries/my/", **auth_headers)
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["delivery_id"] == sample_delivery.delivery_id

def test_get_my_deliveries_unauthorized(api_client):
    """Test getting user's deliveries without authentication"""
    response = api_client.get("/api/v1/deliveries/my/")
    assert response.status_code == 401

def test_create_delivery_admin(api_client, admin_auth_headers):
    """Test creating a delivery as admin"""
    data = {
        "title": "New Delivery",
        "status": "pending",
        "customer_id": "testuser",
        "recipient_name": "John Doe",
        "current_location": {
            "type": "Point",
            "coordinates": [-73.935242, 40.730610]
        },
        "destination": "123 Test St, New York, NY 10001"
    }
    response = api_client.post("/api/v1/deliveries/", data, format="json", **admin_auth_headers)
    assert response.status_code == 201
    assert response.data["title"] == "New Delivery"

def test_create_delivery_unauthorized(api_client):
    """Test creating a delivery without authorization"""
    data = {
        "title": "New Delivery",
        "status": "pending",
        "customer_id": "testuser",
        "recipient_name": "John Doe",
        "current_location": {
            "type": "Point",
            "coordinates": [-73.935242, 40.730610]
        },
        "destination": "123 Test St, New York, NY 10001"
    }
    response = api_client.post("/api/v1/deliveries/", data, format="json")
    assert response.status_code == 401

def test_create_delivery_missing_fields(api_client, admin_auth_headers):
    """Test creating a delivery with missing fields"""
    data = {
        "title": "New Delivery"
        # Missing required fields
    }
    response = api_client.post("/api/v1/deliveries/", data, format="json", **admin_auth_headers)
    assert response.status_code == 400

def test_delete_delivery_admin(api_client, admin_auth_headers, sample_delivery):
    """Test deleting a delivery as admin"""
    response = api_client.delete(f"/api/v1/deliveries/{sample_delivery.delivery_id}/", **admin_auth_headers)
    assert response.status_code == 204
    assert Delivery.objects(delivery_id=sample_delivery.delivery_id).first() is None

def test_delete_delivery_unauthorized(api_client, sample_delivery):
    """Test deleting a delivery without authorization"""
    response = api_client.delete(f"/api/v1/deliveries/{sample_delivery.delivery_id}/")
    assert response.status_code == 401

def test_update_delivery_location_admin(api_client, admin_auth_headers, sample_delivery):
    """Test updating delivery location as admin"""
    data = {
        "location": {
            "type": "Point",
            "coordinates": [-74.006, 40.7128]
        }
    }
    response = api_client.put(
        f"/api/v1/deliveries/{sample_delivery.delivery_id}/location/",
        data,
        format="json",
        **admin_auth_headers
    )
    assert response.status_code == 200
    updated = Delivery.objects(delivery_id=sample_delivery.delivery_id).first()
    assert updated.current_location["coordinates"] == [-74.006, 40.7128]

def test_update_delivery_location_invalid_format(api_client, admin_auth_headers, sample_delivery):
    """Test updating delivery location with invalid format"""
    data = {
        "location": {
            "type": "Invalid",
            "coordinates": [-74.006, 40.7128]
        }
    }
    response = api_client.put(
        f"/api/v1/deliveries/{sample_delivery.delivery_id}/location/",
        data,
        format="json",
        **admin_auth_headers
    )
    assert response.status_code == 400

def test_update_delivery_status_admin(api_client, admin_auth_headers, sample_delivery):
    """Test updating delivery status as admin"""
    data = {
        "status": "in transit",
        "location": {
            "type": "Point",
            "coordinates": [-74.006, 40.7128]
        }
    }
    response = api_client.put(
        f"/api/v1/deliveries/{sample_delivery.delivery_id}/status/",
        data,
        format="json",
        **admin_auth_headers
    )
    assert response.status_code == 200
    updated = Delivery.objects(delivery_id=sample_delivery.delivery_id).first()
    assert updated.status == "in transit"
    assert len(updated.status_history) > 0

def test_update_delivery_invalid_status(api_client, admin_auth_headers, sample_delivery):
    """Test updating delivery with invalid status"""
    data = {
        "status": "invalid_status",
        "location": {
            "type": "Point",
            "coordinates": [-74.006, 40.7128]
        }
    }
    response = api_client.put(
        f"/api/v1/deliveries/{sample_delivery.delivery_id}/status/",
        data,
        format="json",
        **admin_auth_headers
    )
    assert response.status_code == 400

def test_valid_location_format():
    """Test valid location format validation"""
    location = {
        "type": "Point",
        "coordinates": [-73.935242, 40.730610]
    }
    delivery = Delivery(
        delivery_id="TEST123",
        title="Test Delivery",
        status="pending",
        customer_id="testuser",
        recipient_name="John Doe",
        current_location=location,
        destination="123 Test St, New York, NY 10001"
    )
    delivery.save()
    assert delivery.current_location == location

def test_invalid_location_type():
    """Test invalid location type validation"""
    with pytest.raises(Exception):
        Delivery(
            delivery_id="TEST123",
            title="Test Delivery",
            status="pending",
            customer_id="testuser",
            recipient_name="John Doe",
            current_location={
                "type": "Invalid",
                "coordinates": [-73.935242, 40.730610]
            },
            destination="123 Test St, New York, NY 10001"
        ).save()

def test_invalid_coordinates_format():
    """Test invalid coordinates format validation"""
    with pytest.raises(Exception):
        Delivery(
            delivery_id="TEST123",
            title="Test Delivery",
            status="pending",
            customer_id="testuser",
            recipient_name="John Doe",
            current_location={
                "type": "Point",
                "coordinates": [-73.935242]  # Missing latitude
            },
            destination="123 Test St, New York, NY 10001"
        ).save()

def test_status_history_tracking(sample_delivery):
    """Test status history tracking"""
    initial_history_count = len(sample_delivery.status_history)
    
    # Update status
    sample_delivery.status = "in transit"
    sample_delivery.status_history.append(
        StatusHistory(
            status="in transit",
            location=sample_delivery.current_location
        )
    )
    sample_delivery.save()
    
    updated = Delivery.objects(delivery_id=sample_delivery.delivery_id).first()
    assert len(updated.status_history) == initial_history_count + 1
    assert updated.status_history[-1].status == "in transit"
