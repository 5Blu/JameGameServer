import asyncio
import websockets

clients = set()
 
async def handler(ws):
    clients.add(ws)
    try:
        async for message in ws:
            print("Received:", message)

            # Echo back to sender
            await ws.send(f"Server got: {message}\nConnected to Twokie VPS")

            # Or broadcast to everyone:
            # await asyncio.gather(*[c.send(message) for c in clients])

    except websockets.ConnectionClosed:
        print("Client disconnected")
    finally:
        clients.remove(ws)


async def main():
    async with websockets.serve(handler, "::", 6789):
        print("Server running on port 6789")
        await asyncio.Future()  # run forever


asyncio.run(main())
