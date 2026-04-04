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
                break
        if self.active_character is None:
            self.out = True

class Character:
    def __init__(self, chrid, name, health, dmg, income, cards):
        self.chrid = chrid
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
            self.owner.game.say(f"{self.name} has been defeated!")
            if self.owner.active_character is not None:
                self.owner.game.say(f"{self.owner.active_character.name} is now active")
            


    def is_alive(self):
        return self.health > 0

    def createJson(self):
        return {
            "chr_id": self.chrid,
            "name": self.name,
            "dmg": self.dmg,
            "income": self.income,
            "health": self.health,
            "poison": self.poison
        }

class Deck:
    def __init__(self, cards):
        self.cards = cards

class Card:
    def __init__(self, cid, name, cost, effects, text, tgt_slf_dft):
        self.cid = cid
        self.name = name
        self.cost = cost
        self.effects = effects
        self.text = text
        self.tgt_slf_dft = tgt_slf_dft

    def play(self,target):
        for e in self.effects:
            e.do(target)

    def createJson(self):
        return {
            "c_id": self.cid,
            "name": self.name,
            "cost": self.cost,
            "text": self.text,
            "tgt_slf_dft": self.tgt_slf_dft
        }

class Ability:
    def do(self, target):
        print("Error: Ability Parent Class shouldn't be used")
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
        self.listening = False
        self.report = []
        self.log = []
        self.clients = set()

        for p in players:
            p.game = self

    def next_turn(self):
        alive_count = 0 # checks if only 1 player is alive, if so end the game
        for p in self.players:
            if p.out == False:
                alive_count += 1
        if alive_count <= 1:
            self.ended = True
            self.say("Game Over")
            if self.players[0].out:
                self.say(f"{self.players[1].name} wins!")
            elif self.players[1].out:
                self.say(f"{self.players[0].name} wins!")
            else:
                self.say("It's a draw!")
            return False
        else:
            self.current_player_index = (self.current_player_index + 1) % len(self.players) # switch who's turn it is
            return True

    def turn_start(self):
        if self.ended:
            return
        player = self.players[self.current_player_index] # Get the current player and opponent
        opponent = self.players[(self.current_player_index + 1) % len(self.players)]

        opponent.active_character.take_damage(player.active_character.dmg) # Player attacks opponent
        player.gold += player.active_character.income # Player gains gold
        
        self.cards = []
        for i in range(0,3):
            self.cards.append(random.choice(player.active_character.cards))

        self.get_legal_actions()
       
    def get_legal_actions(self):
        if self.ended:
            return
        player = self.players[self.current_player_index] # Get the current player and opponent
        opponent = self.players[(self.current_player_index + 1) % len(self.players)]

        self.say(f"{player.name}'s turn. Active character: {player.active_character.name}, Health: {player.active_character.health}, Gold: {player.gold}")
        self.say(f"Opponent: {opponent.name}, Active character: {opponent.active_character.name}, Health: {opponent.active_character.health}")

        choices = []

        for card in self.cards:
            if card.cost <= player.gold:
                choices.append(Action("Play", card, player))
                choices.append(Action("Play", card, opponent))
            choices.append(Action("Sell", card))
        choices.append(Action("Pass"))
        self.choices = choices
        self.listening = True

    def say(self, message):
        print(message)
        self.report.append(message)
        self.log.append(message)

    def get_statejson(self):
        statejson = []
        for p in self.players:
            p_json = {
                "name": p.name,
                "gold": p.gold,
                "active_character": p.active_character.createJson(),
                "out": p.out
            }
            charjson = []
            for char in p.deck.cards:
                charjson.append(char.createJson())
            p_json["characters"] = charjson
            statejson.append(p_json)
        return statejson




    def action_recieved(self,choice):
        self.listening = False
        self.report = []
        self.report.append(f"{self.players[self.current_player_index].name} chose to {choice.type} {choice.card.name if choice.card else ''} {'targeting ' + choice.target.name if choice.target else ''}")
        player = self.players[self.current_player_index] # Get the current player and opponent
        opponent = self.players[(self.current_player_index + 1) % len(self.players)]

        if choice.type == "Pass":
            poison_amt = player.active_character.poison
            if poison_amt > 0:
                player.active_character.take_damage(poison_amt)
                player.active_character.poison = 0

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
                self.say(choice.card.name)
                self.say(choice.target.name)
            self.get_legal_actions()

    def make_choice(self, choices):
        self.say("Please Choose between")
        for i, c in enumerate(choices):
            if c.target is not None:
                self.say(f"{i}: {c.type} {c.card.name} targeting {c.target.name}")
            elif c.card is not None:
                self.say(f"{i}: {c.type} {c.card.name}")
            else:
                self.say(f"{i}: {c.type}")
        choice = int(input("  > "))
        if choice >= len(choices) or choice < 0:
            self.say("Invalid Choice")
            choice = choices.index(self.make_choice(choices)) # finds the index of the choice that was made when called recuirsively
        if choices[choice].type == "Play" and choices[choice].card.cost > self.players[self.current_player_index].gold:
            self.say("Invalid Choice")
            choice = choices.index(self.make_choice(choices)) # finds the index of the choice that was made when called recuirsively
        return choices[choice]










