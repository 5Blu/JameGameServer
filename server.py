import asyncio
import websockets
from copy import deepcopy
from gamelogic import Game, Player, Character, Deck, Card, DamageAbility, HealAbility, IncomeAbility, PoisonAbility

clients = set() 

Spikes = Card("Spikes", 3, [DamageAbility(2),PoisonAbility(2)], "Deal 2 damage, inflict 2 poison.")
Seawead = Card("Seaweed", 2, [HealAbility(1), IncomeAbility(1)], "Heal 1 health, increase income by 1.")
Bubbles = Card("Bubbles", 2, [DamageAbility(3)], "Deal 3 damage.")

Toxic_Tax = Card("Toxic Tax", 3, [DamageAbility(2), IncomeAbility(-1)], "Deal 2 damage, decrease income by 1.")
Sludge = Card("Sludge", 2, [DamageAbility(1), PoisonAbility(2)], "Deal 1 damage, inflict 2 poison.")
Slimey_Slap = Card("Slimey Slap", 4, [DamageAbility(5)], "Deal 5 damage.")

Puffer = Character("Puffer", 20, 3, 1, [Spikes, Seawead, Bubbles])
Ooze = Character("Ooze", 30, 2, 1, [Toxic_Tax, Sludge, Slimey_Slap])

P1 = Player("Jame", Deck([deepcopy(Puffer), deepcopy(Puffer), deepcopy(Puffer)]))
P2 = Player("SlugMan", Deck([deepcopy(Ooze),deepcopy(Ooze),deepcopy(Ooze)]))

game = Game([P1, P2])
game.turn_start()

async def handler(ws):
    clients.add(ws)
    try:
        async for message in ws:
            print("Received:", message)
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
                game.make_choice(game.choices[message.split(" ")[1]])
                await ws.send(f"Game State: {game.report}")
            else:
                await ws.send("Invalid Choice")

            #await ws.send(f"Server got: {message}\nConnected to Twokie VPS")

    except websockets.ConnectionClosed:
        print("Client disconnected")
    finally:
        clients.remove(ws)


async def main():
    async with websockets.serve(handler, "::", 6789):
        print("Server running on port 6789")
        await asyncio.Future()  # run forever


asyncio.run(main())
