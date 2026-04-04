import asyncio
import websockets
import secrets
from copy import deepcopy
import json
from gamelogic import Game, Player, Character, Deck, Card, DamageAbility, HealAbility, IncomeAbility, PoisonAbility

clients = set()


sessions = {}  
ws_user = {}    

Spikes = Card(1, "Spikes", 3, [DamageAbility(2),PoisonAbility(2)], "Deal 2 damage, inflict 2 poison.", False)
Seawead = Card(2, "Seaweed", 2, [HealAbility(1), IncomeAbility(1)], "Heal 1 health, increase income by 1.", True)
Bubbles = Card(3, "Bubbles", 2, [DamageAbility(3)], "Deal 3 damage.", False)

Toxic_Tax = Card(4, "Toxic Tax", 3, [DamageAbility(2), IncomeAbility(-1)], "Deal 2 damage, decrease income by 1.", False)
Sludge = Card(5, "Sludge", 2, [DamageAbility(1), PoisonAbility(2)], "Deal 1 damage, inflict 2 poison.", False)
Slimey_Slap = Card(6, "Slimey Slap", 4, [DamageAbility(5)], "Deal 5 damage.", False)

Puffer = Character(1, "Puffer", 20, 3, 1, [Spikes, Seawead, Bubbles])
Ooze = Character(2, "Ooze", 30, 2, 1, [Toxic_Tax, Sludge, Slimey_Slap])

P1 = Player("X", Deck([deepcopy(Puffer), deepcopy(Puffer), deepcopy(Puffer)]))
P2 = Player("X", Deck([deepcopy(Ooze),deepcopy(Ooze),deepcopy(Ooze)]))

game = Game([P1, P2])

allcards = [Spikes, Seawead, Bubbles, Toxic_Tax, Sludge, Slimey_Slap]
allcharacters = [Puffer, Ooze]

cardsjson = [card.createJson() for card in allcards]
charactersjson = [char.createJson() for char in allcharacters]
json_data = [cardsjson, charactersjson]

game.turn_start()

async def handler(ws):
    clients.add(ws)
    try:
        async for message in ws:
            print("Received:", message)

            # Auth command: "auth <username>"
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
                        break
                game.clients.add(ws)
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
                await ws.send(f"STATE:{json.dumps(game.get_statejson())}")
            elif message == "get_json":
                await ws.send(f"JSON:{json.dumps(json_data)}")
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
                await broadcast_to_game(game.clients, f"STATE:{json.dumps(game.get_statejson())}")
            elif message.startswith("get_cards"):
                # Server-side authorization: only active player may act
                caller = ws_user[ws]
                current_player_name = game.players[game.current_player_index].name
                if caller != current_player_name:
                    await ws.send("error not your turn")
                    continue
                ids = []
                for c in game.cards:
                    ids.append(c.cid)
                    
                chc = "["
                for i, c in enumerate(game.choices):
                    chc += "{"
                    if c.target is not None:
                        chc += f'"option":{i},"c_id":{c.card.cid},"type":"{c.type}","target":"{c.target.name}"'
                    elif c.card is not None:
                        chc += f'"option":{i},"c_id":{c.card.cid},"type":"{c.type}","target":"None"'
                    else:
                        chc += f'"option":{i},"c_id":"None","type":"{c.type}","target":"None"'
                    chc += "},"
                chc = chc[:-1] + "]"
                await ws.send(f"CARDS:[{ids},{chc}]")
            else:
                await ws.send("Invalid Choice")

    except websockets.ConnectionClosed:
        print("Client disconnected")
    finally:
        clients.discard(ws)
        ws_user.pop(ws, None)

async def broadcast_to_game(g_clients, msg):
    dead = []
    for client in g_clients:
        try:
            await client.send(msg)
        except:
            dead.append(client)

    # clean up disconnected clients
    for d in dead:
        g_clients.discard(d)

async def main():
    async with websockets.serve(handler, None, 6789):
        print("Server running on port 6789")
        await asyncio.Future()  # run forever

asyncio.run(main())
