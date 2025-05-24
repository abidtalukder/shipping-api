from mongoengine import Document, StringField, DateTimeField, DictField, ListField, EmbeddedDocument, EmbeddedDocumentField
from datetime import datetime, timezone

VALID_STATUSES = ['pending', 'in transit', 'out for delivery', 'delivered']

class StatusHistory(EmbeddedDocument):
    """
    Embedded document to track delivery status history.
    """
    status = StringField(required=True, choices=VALID_STATUSES)
    location = DictField(required=True)
    timestamp = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "status": self.status,
            "location": self.location,
            "timestamp": self.timestamp.isoformat()
        }

class Delivery(Document):
    """
    Document to store delivery information.
    """
    delivery_id = StringField(required=True, unique=True)
    title = StringField(required=True, max_length=100)
    status = StringField(required=True, choices=VALID_STATUSES)
    customer_id = StringField(required=True)
    recipient_name = StringField(required=True)
    current_location = DictField(required=True)
    destination = StringField(required=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    last_updated = DateTimeField(default=lambda: datetime.now(timezone.utc))
    status_history = ListField(EmbeddedDocumentField(StatusHistory), default=list)

    meta = {
        "collection": "deliveries",
        "db_alias": "default"
    }

    def to_dict(self):
        return {
            "delivery_id": self.delivery_id,
            "title": self.title,
            "status": self.status,
            "customer_id": self.customer_id,
            "recipient_name": self.recipient_name,
            "current_location": self.current_location,
            "destination": self.destination,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "status_history": [sh.to_dict() for sh in self.status_history]
        }
