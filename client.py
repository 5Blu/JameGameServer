import asyncio
import websockets
from pathlib import Path

SERVER = "ws://[2a02:4780:f:5283::1]:6789"
TOKEN_FILE = Path("session.token")

async def test():
    token = None
    if TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text().strip()

    async with websockets.connect(SERVER) as ws:
        # Try resume if we have a token
        if token:
            await ws.send(f"resume {token}")
            reply = await ws.recv()
            print("Server:", reply)
            if reply.startswith("error"):
                print("Resume failed, will re-authenticate.")
                token = None

        # If no valid token, authenticate
        if not token:
            username = input("Enter username to auth as: ").strip()
            await ws.send(f"auth {username}")
            reply = await ws.recv()
            print("Server:", reply)
            if reply.startswith("auth_ok "):
                token = reply.split(" ", 1)[1].strip()
                TOKEN_FILE.write_text(token)
                print("Saved session token.")
            else:
                print("Auth failed:", reply)
                return

        # Main command loop (unchanged commands)
        while True:
            msg_ind = input("Would you like to:\n1. get_state\n2. get_choices\n3. make_choice\n> ").strip()
            if msg_ind == "1":
                await ws.send("get_state")
            elif msg_ind == "2":
                await ws.send("get_choices")
            elif msg_ind == "3":
                c = input("> ")
                await ws.send("make_choice " + c)
            else:
                await ws.send("invalid choice")

            reply = await ws.recv()
            print("Server:", reply)

asyncio.run(test())
