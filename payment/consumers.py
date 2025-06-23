import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from food.models import Order
from tables.models import Table

class PaymentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'payment_notifications'
        self.room_group_name = f'payment_{self.room_name}'
        
        # Get order_id from query string if available
        self.order_id = self.scope['url_route']['kwargs'].get('order_id', None)
        if self.order_id:
            self.order_group_name = f'order_{self.order_id}'
            await self.channel_layer.group_add(
                self.order_group_name,
                self.channel_name
            )
        
        # Join room group for admin notifications
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room groups
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        if self.order_id:
            await self.channel_layer.group_discard(
                self.order_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']
        
        if message_type == 'payment_success':
            order_id = text_data_json['order_id']
            await self.update_order_status(order_id, True)
            await self.unlock_table(order_id)
            
            # Send message to admin
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'payment_notification',
                    'message': f'Payment successful for Order #{order_id}',
                    'order_id': order_id,
                    'status': 'success'
                }
            )
        
        elif message_type == 'counter_payment':
            order_id = text_data_json['order_id']
            table_number = text_data_json['table_number']
            
            # Send message to admin
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'payment_notification',
                    'message': f'Table number {table_number} yet to pay cash!',
                    'order_id': order_id,
                    'status': 'pending'
                }
            )
    
    async def payment_notification(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'order_id': event['order_id'],
            'status': event['status']
        }))
    
    async def payment_complete(self, event):
        # Send payment complete message to customer
        await self.send(text_data=json.dumps({
            'type': 'payment_complete',
            'message': event['message'],
            'order_id': event['order_id']
        }))
    
    # NEW METHOD: Handle new order notifications
    async def new_order_notification(self, event):
        # Send new order data to admin dashboard
        await self.send(text_data=json.dumps({
            'type': 'new_order',
            'order_data': event['order_data'],
            'message': event['message']
        }))
    
    @database_sync_to_async
    def update_order_status(self, order_id, is_paid):
        order = Order.objects.get(id=order_id)
        order.is_paid = is_paid
        order.save()
    
    @database_sync_to_async
    def unlock_table(self, order_id):
        order = Order.objects.get(id=order_id)
        table = order.table
        table.is_locked = False
        table.locked_by = None
        table.locked_at = None
        table.save()