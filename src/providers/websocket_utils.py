"""
WebSocket utilities to replace om1_utils dependency.
"""

import asyncio
import json
import logging
import websockets
from typing import Any, Callable, Dict, Optional
import threading


class WebSocketClient:
    """Simple WebSocket client to replace om1_utils.ws functionality."""
    
    def __init__(self, url: str):
        """
        Initialize WebSocket client.
        
        Parameters
        ----------
        url : str
            WebSocket URL to connect to
        """
        self.url = url
        self.websocket = None
        self.running = False
        self.message_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        self.connect_callback: Optional[Callable] = None
        self.disconnect_callback: Optional[Callable] = None
        
    def set_message_callback(self, callback: Callable):
        """Set callback for received messages."""
        self.message_callback = callback
        
    def set_error_callback(self, callback: Callable):
        """Set callback for errors."""
        self.error_callback = callback
        
    def set_connect_callback(self, callback: Callable):
        """Set callback for connection events."""
        self.connect_callback = callback
        
    def set_disconnect_callback(self, callback: Callable):
        """Set callback for disconnection events."""
        self.disconnect_callback = callback
    
    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.url)
            self.running = True
            if self.connect_callback:
                self.connect_callback()
            logging.info(f"Connected to WebSocket: {self.url}")
            
            # Start listening for messages
            await self._listen()
            
        except Exception as e:
            logging.error(f"WebSocket connection error: {e}")
            if self.error_callback:
                self.error_callback(e)
    
    async def _listen(self):
        """Listen for incoming messages."""
        try:
            async for message in self.websocket:
                if self.message_callback:
                    try:
                        # Try to parse as JSON
                        data = json.loads(message)
                        self.message_callback(data)
                    except json.JSONDecodeError:
                        # If not JSON, pass as string
                        self.message_callback(message)
        except websockets.exceptions.ConnectionClosed:
            logging.info("WebSocket connection closed")
            if self.disconnect_callback:
                self.disconnect_callback()
        except Exception as e:
            logging.error(f"WebSocket listen error: {e}")
            if self.error_callback:
                self.error_callback(e)
        finally:
            self.running = False
    
    async def send(self, message: Any):
        """
        Send a message through the WebSocket.
        
        Parameters
        ----------
        message : Any
            Message to send (will be JSON serialized if not a string)
        """
        if not self.websocket or not self.running:
            logging.warning("WebSocket not connected")
            return
            
        try:
            if isinstance(message, str):
                await self.websocket.send(message)
            else:
                await self.websocket.send(json.dumps(message))
        except Exception as e:
            logging.error(f"WebSocket send error: {e}")
            if self.error_callback:
                self.error_callback(e)
    
    async def close(self):
        """Close WebSocket connection."""
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        self.running = False
        logging.info("WebSocket connection closed")

    # Compatibility methods to match expected interface
    def register_message_callback(self, callback: Optional[Callable]):
        """Register message callback (compatibility method)."""
        if callback is not None:
            self.set_message_callback(callback)
    
    def send_message(self, message: Any):
        """Send message synchronously (compatibility method)."""
        if not self.running:
            logging.warning("WebSocket not connected, cannot send message")
            return
        # Create a simple sync wrapper for async send
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule the coroutine
                asyncio.create_task(self.send(message))
            else:
                loop.run_until_complete(self.send(message))
        except Exception as e:
            logging.error(f"Error sending WebSocket message: {e}")
    
    def start(self):
        """Start WebSocket connection (compatibility method)."""
        if not self.running:
            # Start in a separate thread
            ws.run_client(self)
            self.running = True
    
    def stop(self):
        """Stop WebSocket connection (compatibility method)."""
        self.running = False
        if self.websocket:
            # Schedule close if there's an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.close())
            except RuntimeError:
                # No event loop, this is fine for cleanup
                pass


# Compatibility wrapper to match om1_utils.ws interface
class ws:
    """WebSocket wrapper to match om1_utils.ws interface."""
    
    # Add Client as an alias to WebSocketClient for compatibility
    Client = WebSocketClient
    
    @staticmethod
    def create_client(url: str) -> WebSocketClient:
        """Create a WebSocket client."""
        return WebSocketClient(url)
    
    @staticmethod
    def run_client(client: WebSocketClient):
        """Run WebSocket client in a separate thread."""
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(client.connect())
            except Exception as e:
                logging.error(f"WebSocket client error: {e}")
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        return thread