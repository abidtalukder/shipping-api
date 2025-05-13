from mongoengine import Document, StringField, EmailField, BooleanField
from datetime import datetime, timezone

class User(Document):
    username = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    password_hash = StringField(required=True)
    is_admin = BooleanField(default=False)
    created_at = StringField(default=lambda: datetime.now(timezone.utc).isoformat())

    meta = {
        "collection": "users",
        "db_alias": "default"
    }

    def __str__(self):
        return self.username
