import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from deliveries.mongo.delivery import Delivery

class DeliveryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.delivery_id = self.scope['url_route']['kwargs']['delivery_id']
        self.room_group_name = f'delivery_{self.delivery_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'subscribe_delivery':
            delivery = await self.get_delivery_info(self.delivery_id)
            if delivery:
                await self.send(text_data=json.dumps({
                    'type': 'delivery_info',
                    'delivery': delivery
                }))

    # Receive message from room group
    async def delivery_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'delivery_update',
            'update_type': event.get('update_type', 'status'),
            'delivery': event.get('delivery'),
            'location': event.get('location'),
            'status': event.get('status'),
            'timestamp': event.get('timestamp')
        }))

    @database_sync_to_async
    def get_delivery_info(self, delivery_id):
        delivery = Delivery.objects(delivery_id=delivery_id).first()
        if delivery:
            return {
                'id': delivery.delivery_id,
                'status': delivery.status,
                'location': delivery.current_location,
                'title': delivery.title,
                'recipient_name': delivery.recipient_name,
                'last_updated': delivery.last_updated.isoformat() if delivery.last_updated else None
            }
        return None 