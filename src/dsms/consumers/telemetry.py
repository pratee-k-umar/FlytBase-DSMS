"""
Telemetry WebSocket Consumer
Handles real-time telemetry streaming to clients.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class TelemetryConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time mission telemetry.
    
    Connect: ws://host/ws/missions/<mission_id>/telemetry/
    
    Receives telemetry updates from the simulator and broadcasts
    them to all connected clients watching the mission.
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.mission_id = self.scope['url_route']['kwargs']['mission_id']
        self.room_group_name = f'mission_{self.mission_id}'
        
        # Join mission room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'mission_id': self.mission_id,
            'message': 'Connected to telemetry stream'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave mission room
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages from client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except json.JSONDecodeError:
            pass
    
    # Handler for telemetry updates (called by simulator)
    async def telemetry_update(self, event):
        """Send telemetry update to WebSocket client"""
        await self.send(text_data=json.dumps({
            'type': 'telemetry',
            'data': event['data']
        }))
    
    # Handler for status changes
    async def status_change(self, event):
        """Send status change to WebSocket client"""
        await self.send(text_data=json.dumps({
            'type': 'status_change',
            'data': event['data']
        }))
    
    # Handler for mission completion
    async def mission_complete(self, event):
        """Send mission completion notification"""
        await self.send(text_data=json.dumps({
            'type': 'mission_complete',
            'data': event['data']
        }))
