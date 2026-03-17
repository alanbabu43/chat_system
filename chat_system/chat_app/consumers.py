import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.other_user_id = int(self.scope['url_route']['kwargs']['user_id'])

        # Create a consistent room name regardless of who initiated the chat
        ids = sorted([self.user.id, self.other_user_id])
        self.room_name = f'chat_{ids[0]}_{ids[1]}'

        # Join room group
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        # Update online status
        await self.set_online_status(True)

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)

        if hasattr(self, 'user') and self.user.is_authenticated:
            await self.set_online_status(False)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type', 'message')

        if msg_type == 'message':
            content = data.get('content', '').strip()
            if not content:
                return

            # Save to DB
            message = await self.save_message(content)

            # Broadcast to room
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'chat_message',
                    'message_id': message.id,
                    'content': content,
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'timestamp': message.timestamp.strftime('%b %d, %Y %H:%M'),
                    'is_read': False,
                }
            )

        elif msg_type == 'read_receipt':
            message_ids = data.get('message_ids', [])
            if message_ids:
                await self.mark_messages_read(message_ids)

                # Notify sender that messages were read
                ids = sorted([self.user.id, self.other_user_id])
                sender_room = f'chat_{ids[0]}_{ids[1]}'
                await self.channel_layer.group_send(
                    sender_room,
                    {
                        'type': 'read_receipt',
                        'message_ids': message_ids,
                        'reader_id': self.user.id,
                    }
                )

        elif msg_type == 'delete_message':
            message_id = data.get('message_id')
            if message_id:
                success = await self.delete_message_async(message_id)
                if success:
                    # Broadcast to room
                    await self.channel_layer.group_send(
                        self.room_name,
                        {
                            'type': 'message_deleted',
                            'message_id': message_id,
                        }
                    )

    async def chat_message(self, event):
        """Receive message from group and send to WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'content': event['content'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp'],
            'is_read': event['is_read'],
        }))

    async def read_receipt(self, event):
        """Broadcast read receipt to room."""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_ids': event['message_ids'],
            'reader_id': event['reader_id'],
        }))

    async def message_deleted(self, event):
        """Broadcast message deleted event to room."""
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id'],
        }))

    @database_sync_to_async
    def save_message(self, content):
        from .models import Message, User
        other_user = User.objects.get(id=self.other_user_id)
        return Message.objects.create(
            sender=self.user,
            receiver=other_user,
            content=content,
        )

    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        from .models import Message
        Message.objects.filter(
            id__in=message_ids,
            receiver=self.user,
            is_read=False
        ).update(is_read=True)

    @database_sync_to_async
    def delete_message_async(self, message_id):
        from .models import Message
        try:
            # Ensure the current user is the sender of the message
            msg = Message.objects.get(id=message_id, sender=self.user)
            msg.delete()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def set_online_status(self, status):
        from .models import User
        User.objects.filter(id=self.user.id).update(
            is_online=status,
            last_seen=timezone.now() if not status else None
        )
