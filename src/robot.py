import asyncio
import websockets

# === Step 2: WebSocket Server ===
async def getData(websocket):
	result = await websocket.recv()
	result = result.split("_")
	print(result)

# === Step 2: WebSocket Server ===
async def main():
	async with websockets.serve(getData, "localhost", 8765):
		print("WebSocket server is running on ws://localhost:8765")
		await asyncio.Future()


if __name__ == "__main__":
	asyncio.run(main())