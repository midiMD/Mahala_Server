import os
import django
import pytest
from rest_framework.authtoken.models import Token
import asyncio
import websockets
import json
import time
from channels.db import database_sync_to_async
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import threading
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mahala_server.settings')
# django.setup()
# from backend.api.models import CustomUser
class WebSocketClient:
    def __init__(self, name, url: str):
        self.name = name
        self.url = url
        self.websocket = None
        self.messages_received = []
        self.messages_sent = []
        self.is_connected = False
        
    async def connect(self):
        """Connect to the WebSocket server"""
        
        self.websocket = await websockets.connect(self.url)
        self.is_connected = True
        return True
        
    
    async def disconnect(self):
        """Disconnect from the WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            
    async def authenticate(self,token):
        """Send a message to the WebSocket server"""
        if not self.is_connected or not self.websocket:
            raise Exception(f"{self.name} disconnected or the websocket is out")
            
        
        
        message_str = json.dumps({"action":"authenticate",
                                  "token":token})
        await self.websocket.send(message_str)
        return True
    async def send_message(self, message: Dict[Any, Any]):
        """Send a message to the WebSocket server"""
        if not self.is_connected or not self.websocket:
            raise Exception(f"{self.name} disconnected or the websocket is out")
            
        
        
        message_str = json.dumps(message)
        await self.websocket.send(message_str)
        self.messages_sent.append({
            'timestamp': time.time(),
            'message': message,
            'name': self.name
        })
        return True
        
    
    async def listen_for_messages(self, duration: float = 0.2):
        """Listen for incoming messages"""
        if not self.is_connected or not self.websocket:
            raise Exception(f"{self.name} disconnected or the websocket is out")
        
        try:
            # Wait for message with timeout
            message = await asyncio.wait_for(self.websocket.recv(), timeout=duration)
            parsed_message = json.loads(message)
            return parsed_message
        except asyncio.TimeoutError:
            raise Exception(f"{self.name} timeout error waiting for message")
        except websockets.exceptions.ConnectionClosed:
            raise Exception(f"{self.name} connection forced shut")
        except json.JSONDecodeError as e:
            raise Exception(f"{self.name} received invalid Json")


@database_sync_to_async
def get_user_by_name(full_name: str):
    """Get user by full name"""
    
    return CustomUser.objects.get(full_name=full_name)
    

@database_sync_to_async
def get_user_token(user):
    """Get or create token for user"""
    
    token, _ = Token.objects.get_or_create(user=user)
    return token.key
    

@pytest.mark.asyncio
@pytest.mark.django_db
async def test_authentication():
    flea_client = WebSocketClient("flea","ws://localhost:8000/ws/chat/")
    connected = await flea_client.connect()
    
    assert connected
    # get Flea's token from the DB
    auth_token = "510b233c67587b282f4fd3d479d44ee7dec20fff"
    # auth_token = await get_user_token(await get_user_by_name("flea"))
    # print(auth_token)
    authentication_request = await flea_client.authenticate(auth_token) 
    assert authentication_request
    authentication_response = await flea_client.listen_for_messages()
    assert authentication_response["type"] == "authentication_successful" 

    await flea_client.disconnect()

