
from copy import deepcopy
import random
class Player:
    def __init__(self, name, deck):
        self.name = name
        self.deck = deck
        self.active_character = deck.cards[0]
        self.gold = 0
        self.out = False

        for char in deck.cards:
            char.owner = self

    def next_char(self):
        self.active_character = None
        for c in self.deck.cards:
            if c.is_alive():
                self.active_character = c
        if self.active_character is None:
            self.out = True

class Character:
    def __init__(self, name, health, dmg, income, cards):
        self.name = name
        self.health = health
        self.dmg = dmg
        self.income = income
        self.cards = cards

        self.poison = 0

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.owner.next_char()
            print(f"{self.name} has been defeated!")
            if self.owner.active_character is not None:
                print(f"{self.owner.active_character.name} is now active")

            

    def is_alive(self):
        return self.health > 0

class Deck:
    def __init__(self, cards):
        self.cards = cards


class Card:
    def __init__(self, name, cost, effects, text):
        self.name = name
        self.cost = cost
        self.effects = effects

    def play(self,target):
        for e in self.effects:
            e.do(target)

class Ability:
    def do(self):
        print("Error: Ability Parent Class shouldnt be used")
class DamageAbility(Ability):
    def __init__(self, damage):
        self.damage = damage

    def do(self, target):
        target.active_character.take_damage(self.damage)
class HealAbility(Ability):
    def __init__(self, heal):
        self.heal = heal

    def do(self, target):
        target.active_character.health += self.heal
class IncomeAbility(Ability):
    def __init__(self, income_boost):
        self.income_boost = income_boost

    def do(self, target):
        target.active_character.income += self.income_boost
class PoisonAbility(Ability):
    def __init__(self, poison):
        self.poison = poison

    def do(self, target):
        target.active_character.poison += self.poison

class Action:
    def __init__(self, type, card = None, target = None):
        self.type = type
        self.card = card
        self.target = target

class Game:
    def __init__(self, players):
        self.players = players
        self.current_player_index = 0
        self.ended = False
        self.choices = []
        self.cards = []

    def next_turn(self):
        alive_count = 0 # checks if only 1 player is alive, if so end the game
        for p in self.players:
            if p.out == False:
                alive_count += 1
        if alive_count <= 1:
            self.ended = True
            return False
        else:
            self.current_player_index = (self.current_player_index + 1) % len(self.players) # switch who's turn it is
            return True

    def turn_start(self):
        player = self.players[self.current_player_index] # Get the current player and opponent
        opponent = self.players[(self.current_player_index + 1) % len(self.players)]

        opponent.active_character.take_damage(player.active_character.dmg) # Player attacks opponent
        player.gold += player.active_character.income # Player gains gold
        
        self.cards = []
        for i in range(0,3):
            self.cards.append(random.choice(player.active_character.cards))

        self.get_legal_actions()
       
    def get_legal_actions(self):
        player = self.players[self.current_player_index] # Get the current player and opponent
        opponent = self.players[(self.current_player_index + 1) % len(self.players)]

        print(f"{player.name}'s turn. Active character: {player.active_character.name}, Health: {player.active_character.health}, Gold: {player.gold}")
        print(f"Opponent: {opponent.name}, Active character: {opponent.active_character.name}, Health: {opponent.active_character.health}")

        choices = []

        for card in self.cards:
            if card.cost <= player.gold:
                choices.append(Action("Play", card, player))
                choices.append(Action("Play", card, opponent))
            choices.append(Action("Sell", card))
        choices.append(Action("Pass"))
        self.choices = choices



    def action_recieved(self,choice):
        player = self.players[self.current_player_index] # Get the current player and opponent
        opponent = self.players[(self.current_player_index + 1) % len(self.players)]

        if choice.type == "Pass":
            player.active_character.take_damage(player.active_character.poison) # Apply poison damage at the end of the turn
            self.next_turn()
            self.turn_start()
        else:
            if choice.type == "Sell":
                player.gold += 1
                self.cards.remove(choice.card)
            elif choice.type == "Play":
                player.gold -= choice.card.cost
                self.cards.remove(choice.card)
                choice.card.play(choice.target)
                print(choice.card.name)
                print(choice.target.name)
            self.get_legal_actions()


    def make_choice(self, choices):
        print("Please Choose between")
        for i, c in enumerate(choices):
            if c.target is not None:
                print(f"{i}: {c.type} {c.card.name} targeting {c.target.name}")
            elif c.card is not None:
                print(f"{i}: {c.type} {c.card.name}")
            else:
                print(f"{i}: {c.type}")
        choice = int(input("  > "))
        if choice >= len(choices) or choice < 0:
            print("Invalid Choice")
            choice = choices.index(self.make_choice(choices)) # finds the index of the choice that was made when called recuirsively
        if choices[choice].type == "Play" and choices[choice].card.cost > self.players[self.current_player_index].gold:
            print("Invalid Choice")
            choice = choices.index(self.make_choice(choices)) # finds the index of the choice that was made when called recuirsively
        return choices[choice]



        print("Game Over")
        if self.players[0].out:
            print(f"{self.players[1].name} wins!")
        elif self.players[1].out:
            print(f"{self.players[0].name} wins!")
        else:
            print("It's a draw!")



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


while True:
    input("> ")
    game.action_recieved(game.make_choice(game.choices))