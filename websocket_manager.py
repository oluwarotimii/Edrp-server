import asyncio
import json
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from utils.redis_client import redis_client
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Store user IDs by WebSocket instance
        self.connection_to_user: Dict[WebSocket, int] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a new WebSocket and associate it with a user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        self.connection_to_user[websocket] = user_id
        
        logger.info(f"User {user_id} connected. Total connections: {len(self.connection_to_user)}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket and remove from user mapping"""
        user_id = self.connection_to_user.get(websocket)
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:  # Remove empty lists
                del self.active_connections[user_id]
        
        if websocket in self.connection_to_user:
            del self.connection_to_user[websocket]
        
        logger.info(f"WebSocket disconnected. Remaining connections: {len(self.connection_to_user)}")
    
    async def send_personal_message(self, message: str, user_id: int):
        """Send a message to a specific user"""
        connections = self.active_connections.get(user_id, [])
        disconnected_connections = []
        
        for connection in connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected_connections.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected users"""
        disconnected_connections = []
        
        for connection in self.connection_to_user.keys():
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected_connections.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)

# Global WebSocket manager instance
manager = ConnectionManager()

class ChatManager:
    """Handles chat-specific WebSocket functionality"""
    
    def __init__(self):
        self.redis_client = redis_client
    
    async def handle_chat_message(self, websocket: WebSocket, user_id: int, data: dict):
        """Handle incoming chat messages"""
        try:
            message_type = data.get("type", "message")
            content = data.get("content", "")
            recipient_id = data.get("recipient_id")
            timestamp = data.get("timestamp")
            
            # Create message object
            message_obj = {
                "type": message_type,
                "sender_id": user_id,
                "recipient_id": recipient_id,
                "content": content,
                "timestamp": timestamp or asyncio.get_event_loop().time(),
                "message_id": f"{user_id}_{int(asyncio.get_event_loop().time())}"
            }
            
            # Store message in Redis for persistence
            message_key = f"chat:message:{message_obj['message_id']}"
            await self.redis_client.set_json(message_key, message_obj, expire=86400)  # Expire in 24 hours
            
            # If it's a direct message, send to recipient
            if recipient_id:
                await self.send_direct_message(message_obj)
            else:
                # Broadcast to all connected users (for system notifications)
                await self.broadcast_message(message_obj)
                
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to process message"
            }))
    
    async def send_direct_message(self, message_obj: dict):
        """Send a direct message to a specific user"""
        recipient_id = message_obj["recipient_id"]
        message_json = json.dumps(message_obj)
        
        # Send via WebSocket if recipient is connected
        await manager.send_personal_message(message_json, recipient_id)
        
        # Also publish to Redis for other services to consume
        await self.redis_client.publish(f"chat:direct:{recipient_id}", message_json)
    
    async def broadcast_message(self, message_obj: dict):
        """Broadcast a message to all connected users"""
        message_json = json.dumps(message_obj)
        
        # Send to all connected users via WebSocket
        await manager.broadcast(message_json)
        
        # Also publish to Redis for other services to consume
        await self.redis_client.publish("chat:global", message_json)
    
    async def send_notification(self, user_id: int, notification_data: dict):
        """Send a notification to a specific user"""
        notification_obj = {
            "type": "notification",
            "user_id": user_id,
            "data": notification_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        message_json = json.dumps(notification_obj)
        
        # Send via WebSocket
        await manager.send_personal_message(message_json, user_id)
        
        # Also publish to Redis
        await self.redis_client.publish(f"notification:{user_id}", message_json)

# Global chat manager instance
chat_manager = ChatManager()
