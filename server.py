import asyncio
import websockets
import secrets
from copy import deepcopy
from gamelogic import Game, Player, Character, Deck, Card, DamageAbility, HealAbility, IncomeAbility, PoisonAbility

clients = set()

# In-memory session store and connection map
sessions = {}   # token -> username
ws_user = {}    # websocket -> username

# (keep your existing game setup unchanged)
Spikes = Card("Spikes", 3, [DamageAbility(2),PoisonAbility(2)], "Deal 2 damage, inflict 2 poison.")
Seawead = Card("Seaweed", 2, [HealAbility(1), IncomeAbility(1)], "Heal 1 health, increase income by 1.")
Bubbles = Card("Bubbles", 2, [DamageAbility(3)], "Deal 3 damage.")

Toxic_Tax = Card("Toxic Tax", 3, [DamageAbility(2), IncomeAbility(-1)], "Deal 2 damage, decrease income by 1.")
Sludge = Card("Sludge", 2, [DamageAbility(1), PoisonAbility(2)], "Deal 1 damage, inflict 2 poison.")
Slimey_Slap = Card("Slimey Slap", 4, [DamageAbility(5)], "Deal 5 damage.")

Puffer = Character("Puffer", 20, 3, 1, [Spikes, Seawead, Bubbles])
Ooze = Character("Ooze", 30, 2, 1, [Toxic_Tax, Sludge, Slimey_Slap])

P1 = Player("X", Deck([deepcopy(Puffer), deepcopy(Puffer), deepcopy(Puffer)]))
P2 = Player("X", Deck([deepcopy(Ooze),deepcopy(Ooze),deepcopy(Ooze)]))

game = Game([P1, P2])
game.turn_start()

async def handler(ws):
    clients.add(ws)
    try:
        async for message in ws:
            print("Received:", message)

            # Auth command (prototype): "auth <username>" -> server returns "auth_ok <token>"
            if message.startswith("auth "):
                username = message.split(" ", 1)[1].strip()
                if not username:
                    await ws.send("error missing username")
                    continue
                token = secrets.token_urlsafe(32)
                sessions[token] = username
                ws_user[ws] = username
                for p in game.players:
                    if p.name == "X":
                        p.name = username
                await ws.send(f"auth_ok {token}")
                continue

            # Resume command: "resume <token>"
            if message.startswith("resume "):
                token = message.split(" ", 1)[1].strip()
                username = sessions.get(token)
                if username is None:
                    await ws.send("error invalid token")
                    continue
                ws_user[ws] = username
                await ws.send(f"resume_ok {username}")
                continue

            # Require authentication for other commands
            if ws not in ws_user:
                await ws.send("error not authenticated (send 'auth <username>' or 'resume <token>')")
                continue

            # Existing commands (now authenticated)
            if message == "get_state":
                await ws.send(f"Game State: {game.report}")
            elif message == "get_choices":
                str_c = []
                for i, c in enumerate(game.choices):
                    if c.target is not None:
                        str_c.append(f"{i}: {c.type} {c.card.name} targeting {c.target.name}")
                    elif c.card is not None:
                        str_c.append(f"{i}: {c.type} {c.card.name}")
                    else:
                        str_c.append(f"{i}: {c.type}")
                await ws.send(f"Choices: {str_c}")
            elif message.startswith("make_choice"):
                # Server-side authorization: only active player may act
                caller = ws_user[ws]
                current_player_name = game.players[game.current_player_index].name
                if caller != current_player_name:
                    await ws.send("error not your turn")
                    continue

                parts = message.split(" ")
                if len(parts) < 2:
                    await ws.send("error missing choice index")
                    continue
                try:
                    idx = int(parts[1])
                except ValueError:
                    await ws.send("error invalid choice index")
                    continue
                if idx < 0 or idx >= len(game.choices):
                    await ws.send("error choice index out of range")
                    continue

                game.action_recieved(game.choices[idx])
                await ws.send(f"Game State: {game.report}")
            else:
                await ws.send("Invalid Choice")

    except websockets.ConnectionClosed:
        print("Client disconnected")
    finally:
        clients.discard(ws)
        ws_user.pop(ws, None)

async def main():
    async with websockets.serve(handler, "::", 6789):
        print("Server running on port 6789")
        await asyncio.Future()  # run forever

asyncio.run(main())
