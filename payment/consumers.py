import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from food.models import Order
from tables.models import Table

class PaymentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # COMPLETELY ISOLATED - NO USER/SESSION DATA AT ALL
        print(f"WebSocket connecting - Channel: {self.channel_name}")
        print(f"NO USER DATA STORED - Completely isolated from HTTP sessions")
        
        self.room_name = 'payment_notifications'
        self.room_group_name = f'payment_{self.room_name}'
        
        # Get order_id from URL if available
        self.order_id = self.scope['url_route']['kwargs'].get('order_id', None)
        if self.order_id:
            self.order_group_name = f'order_{self.order_id}'
            await self.channel_layer.group_add(
                self.order_group_name,
                self.channel_name
            )
            print(f"Added to order group: {self.order_group_name}")
        
        # Join room group for admin notifications
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        print(f"Added to notifications group: {self.room_group_name}")
        
        await self.accept()
        print(f"WebSocket connected - Channel: {self.channel_name}")
    
    async def disconnect(self, close_code):
        # Clean disconnect
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        if self.order_id:
            await self.channel_layer.group_discard(
                self.order_group_name,
                self.channel_name
            )
        
        print(f"WebSocket disconnected - Channel: {self.channel_name}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data['type']
            
            print(f"Received: {message_type} on channel: {self.channel_name}")
            
            if message_type == 'payment_success':
                order_id = data['order_id']
                await self.handle_payment_success(order_id)
                
            elif message_type == 'counter_payment':
                order_id = data['order_id']
                table_number = data['table_number']
                await self.handle_counter_payment(order_id, table_number)
                
        except Exception as e:
            print(f"WebSocket receive error: {e}")
    
    async def handle_payment_success(self, order_id):
        """Handle QR payment success"""
        print(f"Handling payment success for order: {order_id}")
        
        await self.update_order_status(order_id, True)
        await self.unlock_table(order_id)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'payment_notification',
                'message': f'Payment successful for Order #{order_id}',
                'order_id': order_id,
                'status': 'success'
            }
        )
    
    async def handle_counter_payment(self, order_id, table_number):
        """Handle counter payment notification"""
        print(f"Handling counter payment for order: {order_id}, table: {table_number}")
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'payment_notification',
                'message': f'Table number {table_number} yet to pay cash!',
                'order_id': order_id,
                'status': 'pending'
            }
        )
    
    # WebSocket message handlers - NO SESSION INTERFERENCE
    async def payment_notification(self, event):
        try:
            await self.send(text_data=json.dumps({
                'message': event['message'],
                'order_id': event['order_id'],
                'status': event['status']
            }))
        except Exception as e:
            print(f"Error sending notification: {e}")
    
    async def payment_complete(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'payment_complete',
                'message': event['message'],
                'order_id': event['order_id']
            }))
        except Exception as e:
            print(f"Error sending payment complete: {e}")
    
    async def new_order_notification(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'new_order',
                'order_data': event['order_data'],
                'message': event['message']
            }))
        except Exception as e:
            print(f"Error sending new order: {e}")
    
    @database_sync_to_async
    def update_order_status(self, order_id, is_paid):
        """Update order status - isolated database operation"""
        try:
            order = Order.objects.get(id=order_id)
            order.is_paid = is_paid
            order.save()
            print(f"Order {order_id} marked as paid: {is_paid}")
        except Exception as e:
            print(f"Error updating order: {e}")
    
    @database_sync_to_async
    def unlock_table(self, order_id):
        """Unlock table - isolated database operation"""
        try:
            order = Order.objects.get(id=order_id)
            table = order.table
            table.is_locked = False
            table.locked_by = None
            table.locked_at = None
            table.save()
            print(f"Table {table.table_number} unlocked")
        except Exception as e:
            print(f"Error unlocking table: {e}")