import json
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from api.models import CustomUser
from .models import Room, Message
from .serializers import RoomSerializer, MessageSerializer
from rest_framework.authtoken.models import Token

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_auth = False
        
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_names'):
            for room_group_name in self.room_group_names:
                await self.channel_layer.group_discard(
                    room_group_name,
                    self.channel_name
                )
        if self.is_auth and hasattr(self, 'user') and hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    #@database_sync_to_async
    def get_user_channel_name(self, user):
        # Get the WebSocket channel name for the user (if they are connected)
        return self.user_channel_map.get(user.id)
    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            # Query the Token model to find the user associated with the token
            token_obj = Token.objects.get(key=token)
            
            return token_obj.user
        except Token.DoesNotExist:
            # Token is invalid or does not exist
            return None
    @database_sync_to_async
    def get_user_from_user_id(self, user_id):
        
        user = CustomUser.objects.get(pk=user_id)
        
        return user
    

    @database_sync_to_async
    def get_user_rooms(self, user):
        rooms = Room.objects.filter(
            Q(user_1=user) | Q(user_2=user)
        ).order_by('-last_message_time')
        serializer = RoomSerializer(rooms, many=True, context={'user': user})
        return serializer.data
    
    @database_sync_to_async
    def get_room_by_users(self,user1: CustomUser, user2: CustomUser):
        room = Room.objects.filter(
            (Q(user_1=user1) & Q(user_2=user2)) | (Q(user_1=user2) & Q(user_2=user1))
        ).first()
        return room
    
    @database_sync_to_async
    def create_room_with_users(self,user1: CustomUser, user2: CustomUser):
        room = Room.objects.create(user_1=user1, user_2=user2)
        return room
    


    @database_sync_to_async
    def get_room_messages(self, room_id, user):
        room = Room.objects.get(id=room_id)
        month_ago = timezone.now() - timedelta(days=30)
        messages = Message.objects.filter(
            room=room,
            timestamp__gte=month_ago
        ).order_by('-timestamp')
        
        # Mark messages as read
        Message.objects.filter(
            room=room,
            unread=True
        ).exclude(sender=user).update(unread=False)
        
        return MessageSerializer(messages, many=True).data

    @database_sync_to_async
    def save_message(self, room_id, user, content):
        room = Room.objects.get(id=room_id)
        message = Message.objects.create(
            room=room,
            sender=user,
            content=content,
            unread=True
        )
        room.last_message_time = message.timestamp
        room.save()
        return MessageSerializer(message).data

    async def process_message(self, data):
        action = data.get('action')

        if action == 'authenticate':
            token = data.get('token')
            self.user = await self.get_user_from_token(token)
            if self.user:
                self.user_group_name = f"user_{self.user.id}"
                self.is_auth = True
                self.room_group_names = []
                rooms = await self.get_user_rooms(self.user)
                
                # Join all room groups
                for room in rooms:
                    room_group_name = f"chat_{room['id']}"
                    self.room_group_names.append(room_group_name)
                    await self.channel_layer.group_add(
                        room_group_name,
                        self.channel_name
                    )
                # Add user's channel to their individual user group. This is done so that we can send messages to individual users.
                # Channels change at every connection so we can't track a user by channel but we can track a user by their user group name
                await self.channel_layer.group_add(
                    self.user_group_name, # we add this channel to the user's group
                    self.channel_name
                )   
                await self.send(json.dumps({
                    'type': 'authentication_successful',
                    'rooms': rooms
                }))
            else:
                await self.send(json.dumps({
                    'type': 'authentication_failed'
                }))

        elif action == 'fetch_messages':
            room_id = data.get('room_id')
            messages = await self.get_room_messages(room_id, self.user)
            await self.send(json.dumps({
                'type': 'messages',
                'room_id': room_id,
                'messages': messages
            }))
        elif action== "subscribe_to_room": # subscribe currently authenticated user to a particular room
            # This will be called when another user sends a message to this user
            # and the user is not currently in the room.
            room_id = data.get('room_id')
            room = Room.objects.get(id=room_id)
            room_group_name = f"chat_{room.id}"
            await self.channel_layer.group_add(
                room_group_name,
                self.channel_name
            )
            room_messages = await self.get_room_messages(room.id,self.user)
            await self.send(json.dumps({
                'type': 'messages',
                'room_id': room.id,
                'messages': room_messages
            }))
        elif action == 'create_or_get_room': # will be called when a user clicks on CHAT button of an item.
            # searches for an existing room with the other user or creates one

            other_user = await self.get_user_from_user_id(data.get('other_id'))
            print(f'''Other user: {other_user}''')
            if other_user is None or self.user is None:
                await self.send(json.dumps({
                    "error":"not_found"
                }))
            else:
                room = await self.get_room_by_users(self.user, other_user)
                if not room:
                    #Create room because one doesn't already exist between the 2 users
                    room = await self.create_room_with_users(self.user, other_user)
                    await self.send(json.dumps({
                        'type': 'room_created',
                        'room_id': room.id
                    }))
                    # Notify User B's Consumer instance about the new room so they can add themselves to the Channel group of that room
                    other_user_group_name = f"user_{other_user.id}"
                
                    await self.channel_layer.group_send(
                        other_user_group_name,
                        {
                            'type': 'added_to_room_notification',
                            'room_id': room.id
                        }
                    )
                else:
                    room_messages = await self.get_room_messages(room.id,self.user)
                    await self.send(json.dumps({
                        'type': 'messages',
                        'room_id': room.id,
                        'messages': room_messages
                    }))

                # Add User A (current user) to the group
                room_group_name = f"chat_{room.id}"
                # Add User A (current user) to the group
                await self.channel_layer.group_add(
                    room_group_name,
                    self.channel_name
                )
                
        elif action == 'send_message':
            room_id = data.get('room_id')
            content = data.get('content')
            message = await self.save_message(room_id, self.user, content)
            await self.send(json.dumps({
                    'type': 'message_success',
                    'room_id': room_id
                }))
            # Broadcast to room Channel group
            await self.channel_layer.group_send(
                f"chat_{room_id}",
                {
                    'type': 'chat_message',
                    'message': message
                }
            )
    # All of these below are responses to group_send calls i.e. on the backend, when another consumer instance(i..e another user's) wants to talk to this user's consumer instance
    async def receive(self, text_data):
        data = json.loads(text_data)
        try:
            await self.process_message(data)
        except Exception as e:
            # Catch any exception that might occur
            error_message = str(e)
            stack_trace = traceback.format_exc()
            print(stack_trace)
            # Send error message back to the client
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': error_message,

            }))
    async def chat_message(self, event): # in response to group_send of type = chat_message
        message = event['message']
        await self.send(json.dumps({
            'type': 'new_message',
            'message': message
        }))
    # In response to group_send of type = added_to_room_notification
    async def added_to_room_notification(self, event):
        # add the user's channel to the room group
        room_id = event['room_id']
        room_group_name = f"chat_{room_id}"
        await self.channel_layer.group_add(
            room_group_name,
            self.channel_name
        )

        await self.send(json.dumps({
            'type': 'joined_room',
            'room_id': event['room_id'],
        }))
            