#!/usr/bin/env python3
"""
Simple WebSocket test client to verify the connection works
"""

import asyncio
import websockets
import json

async def test_websocket():
    """Test WebSocket connection to the game server"""
    try:
        async with websockets.connect("ws://localhost:8000/ws") as websocket:
            print("✓ Connected to WebSocket server")
            
            # Send a test message
            await websocket.send(json.dumps({"type": "request_game_state"}))
            print("✓ Sent test message")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✓ Received response: {data['type']}")
            
            print("✓ WebSocket test successful!")
            
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
