from mongoengine import Document, StringField, DateTimeField, PointField, ListField, EmbeddedDocument, EmbeddedDocumentField
import datetime

class StatusHistory(EmbeddedDocument):
    status = StringField(choices=["pending", "in transit", "out for delivery", "delivered"], required=True)
    timestamp = DateTimeField(default=lambda: datetime.datetime.now(datetime.timezone.utc))
    location = PointField(required=True)  # GeoJSON format: {"type": "Point", "coordinates": [lng, lat]}

    def to_dict(self):
        return {
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "location": self.location
        }

class Delivery(Document):
    delivery_id = StringField(required=True, unique=True)
    title = StringField(required=True, max_length=100)
    status = StringField(choices=["pending", "in transit", "out for delivery", "delivered"])
    customer_id = StringField(null=True)  # optional
    recipient_name = StringField(required=True, max_length=100)

    created_at = DateTimeField(default=datetime.datetime.now(datetime.timezone.utc))
    last_updated = DateTimeField(default=datetime.datetime.now(datetime.timezone.utc))

    current_location = PointField(required=True)
    destination = StringField(required=True)
    status_history = ListField(EmbeddedDocumentField(StatusHistory))

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
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "current_location": self.current_location,
            "destination": self.destination,
            "status_history": [status.to_dict() for status in self.status_history]
        }
