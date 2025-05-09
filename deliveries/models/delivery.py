from mongoengine import Document, StringField, DateTimeField, PointField, ListField, EmbeddedDocument, EmbeddedDocumentField
import datetime

class StatusHistory(EmbeddedDocument):
    status = StringField(choices=["pending", "in transit", "out for delivery", "delivered"])
    timestamp = DateTimeField(default=lambda: datetime.datetime.now(datetime.timezone.utc))
    location = PointField(required=True)  # GeoJSON format: {"type": "Point", "coordinates": [lng, lat]}

class Delivery(Document):
    delivery_id = StringField(required=True, unique=True)
    title = StringField()
    status = StringField(choices=["pending", "in transit", "out for delivery", "delivered"])
    customer_id = StringField(null=True)  # optional
    recipient_name = StringField()

    created_at = DateTimeField(default=datetime.datetime.now(datetime.timezone.utc))
    last_updated = DateTimeField(default=datetime.datetime.now(datetime.timezone.utc))

    current_location = PointField()
    status_history = ListField(EmbeddedDocumentField(StatusHistory))

    meta = {
        "collection": "deliveries",
        "db_alias": "default"
    }
