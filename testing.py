import asyncio
import websockets
import json

async def test_connection():
    try:
        async with websockets.connect('ws://localhost:42069/api') as ws:
            print("Connected!")
            while True:
                data = await ws.recv()
                event = json.loads(data)
                print(f"Event: {event}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_connection())