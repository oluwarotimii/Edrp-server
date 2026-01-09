from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict
import json
import asyncio
from utils.dependencies import get_current_user
from models.user import User
from websocket_manager import manager, chat_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, current_user: User = Depends(get_current_user)):
    """
    WebSocket endpoint for real-time communication
    - user_id: The ID of the user connecting
    - Requires authentication via dependency
    """
    # Verify that the connecting user matches the specified user_id
    if current_user.id != user_id:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse the incoming message
                message_data = json.loads(data)
                
                # Handle different message types
                message_type = message_data.get("type", "message")
                
                if message_type == "message":
                    # Handle chat message
                    await chat_manager.handle_chat_message(websocket, user_id, message_data)
                elif message_type == "ping":
                    # Respond to ping
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message_type == "request_history":
                    # Handle request for chat history
                    # This would typically fetch from database/Redis
                    await websocket.send_text(json.dumps({
                        "type": "history",
                        "messages": []  # In a real implementation, fetch actual history
                    }))
                else:
                    # Unknown message type
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Error processing message"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"User {user_id} disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket)

@router.websocket("/ws/notifications/{user_id}")
async def notification_websocket_endpoint(websocket: WebSocket, user_id: int, current_user: User = Depends(get_current_user)):
    """
    WebSocket endpoint specifically for notifications
    - user_id: The ID of the user connecting
    - Requires authentication via dependency
    """
    # Verify that the connecting user matches the specified user_id
    if current_user.id != user_id:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # For notification WebSocket, we mainly send notifications
            # Receive any control messages if needed
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type")
                
                if message_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                else:
                    # For notification WebSocket, we don't expect regular messages
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "This endpoint is for notifications only"
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"User {user_id} disconnected from notification WebSocket")
    except Exception as e:
        logger.error(f"Notification WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket)
