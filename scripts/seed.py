import os
import sys
import django
import random
import logging
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_backend.settings')
django.setup()

from users.mongo.user import User
from deliveries.mongo.delivery import Delivery, StatusHistory

logger = logging.getLogger('seed')

def clean_database():
    """Remove all data from the database"""
    logger.info("Cleaning database...")
    User.objects.delete()
    Delivery.objects.delete()
    logger.info("Database cleaned")

def create_test_users():
    """Create various types of users for testing"""
    users = []
    
    # Regular user
    regular_user = User(
        username="regular_user",
        email="regular@test.com",
        password_hash="hashed_password",
        is_admin=False
    ).save()
    users.append(regular_user)

    # Admin user
    admin_user = User(
        username="admin_user",
        email="admin@test.com",
        password_hash="hashed_password",
        is_admin=True
    ).save()
    users.append(admin_user)

    # User with many deliveries
    bulk_user = User(
        username="bulk_user",
        email="bulk@test.com",
        password_hash="hashed_password",
        is_admin=False
    ).save()
    users.append(bulk_user)

    # User with special characters
    special_user = User(
        username="user@special#$",
        email="special@test.com",
        password_hash="hashed_password",
        is_admin=False
    ).save()
    users.append(special_user)

    logger.info(f"Created {len(users)} test users")
    return users

def create_test_deliveries(users):
    """Create various types of deliveries for testing"""
    deliveries = []
    statuses = ['pending', 'in transit', 'out for delivery', 'delivered']
    
    def create_status_history(status, location, timestamp):
        return StatusHistory(
            status=status,
            location=location,
            timestamp=timestamp
        )

    # Basic delivery for each status
    for status in statuses:
        delivery = Delivery(
            delivery_id=f"DEL{random.randint(100000, 999999)}",
            title=f"Test Delivery - {status}",
            status=status,
            customer_id=users[0].username,
            recipient_name="John Doe",
            current_location={
                "type": "Point",
                "coordinates": [-73.935242, 40.730610]  # NYC coordinates
            },
            destination="350 5th Ave, New York, NY 10118",  # Empire State Building
            last_updated=timezone.now(),
            status_history=[
                create_status_history(
                    status,
                    {"type": "Point", "coordinates": [-73.935242, 40.730610]},
                    timezone.now()
                )
            ]
        ).save()
        deliveries.append(delivery)

    # Delivery with multiple status updates
    multi_status = Delivery(
        delivery_id=f"DEL{random.randint(100000, 999999)}",
        title="Multi-Status Delivery",
        status="in transit",
        customer_id=users[0].username,
        recipient_name="Jane Smith",
        current_location={
            "type": "Point",
            "coordinates": [-73.935242, 40.730610]
        },
        destination="30 Rockefeller Plaza, New York, NY 10112",  # 30 Rock
        last_updated=timezone.now(),
        status_history=[
            create_status_history(
                "pending",
                {"type": "Point", "coordinates": [-73.935242, 40.730610]},
                timezone.now() - timedelta(hours=2)
            ),
            create_status_history(
                "in transit",
                {"type": "Point", "coordinates": [-73.95, 40.74]},
                timezone.now() - timedelta(hours=1)
            ),
            create_status_history(
                "in transit",
                {"type": "Point", "coordinates": [-73.96, 40.75]},
                timezone.now()
            )
        ]
    ).save()
    deliveries.append(multi_status)

    # Bulk deliveries for one user
    for i in range(20):
        delivery = Delivery(
            delivery_id=f"DEL{random.randint(100000, 999999)}",
            title=f"Bulk Delivery {i+1}",
            status=random.choice(statuses),
            customer_id=users[2].username,  # bulk_user
            recipient_name=f"Recipient {i+1}",
            current_location={
                "type": "Point",
                "coordinates": [
                    random.uniform(-74.1, -73.9),
                    random.uniform(40.6, 40.9)
                ]
            },
            destination=f"{random.randint(1, 999)} Broadway, New York, NY {random.randint(10000, 10999)}",
            last_updated=timezone.now(),
            status_history=[
                create_status_history(
                    random.choice(statuses),
                    {"type": "Point", "coordinates": [-73.935242, 40.730610]},
                    timezone.now() - timedelta(hours=random.randint(1, 24))
                )
            ]
        ).save()
        deliveries.append(delivery)

    # Edge cases
    # 1. Delivery with special characters
    special_delivery = Delivery(
        delivery_id=f"DEL{random.randint(100000, 999999)}",
        title="Special Characters !@#$%^&*()",
        status="pending",
        customer_id=users[3].username,
        recipient_name="Special Name !@#$",
        current_location={
            "type": "Point",
            "coordinates": [-73.935242, 40.730610]
        },
        destination="123 !@#$ Street, New York, NY 10001",
        last_updated=timezone.now()
    ).save()
    deliveries.append(special_delivery)

    # 2. Delivery with long title
    long_title_delivery = Delivery(
        delivery_id=f"DEL{random.randint(100000, 999999)}",
        title="x" * 100,  # Maximum length title
        status="pending",
        customer_id=users[0].username,
        recipient_name="Long Title Test",
        current_location={
            "type": "Point",
            "coordinates": [-73.935242, 40.730610]
        },
        destination="456 Long Title Road, New York, NY 10002",
        last_updated=timezone.now()
    ).save()
    deliveries.append(long_title_delivery)

    # 3. Delivery with same origin and destination
    same_location = {
        "type": "Point",
        "coordinates": [-73.935242, 40.730610]
    }
    same_location_delivery = Delivery(
        delivery_id=f"DEL{random.randint(100000, 999999)}",
        title="Same Location Delivery",
        status="pending",
        customer_id=users[0].username,
        recipient_name="Same Location Test",
        current_location=same_location,
        destination="789 Same Place Street, New York, NY 10003",
        last_updated=timezone.now()
    ).save()
    deliveries.append(same_location_delivery)

    logger.info(f"Created {len(deliveries)} test deliveries")
    return deliveries

def run_seed():
    """Main function to run the seed script"""
    logger.info("Starting seed process...")
    clean_database()
    users = create_test_users()
    deliveries = create_test_deliveries(users)
    logger.info("Seed completed successfully")

if __name__ == "__main__":
    run_seed() 