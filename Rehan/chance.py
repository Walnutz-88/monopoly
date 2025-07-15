import random
from dataclasses import dataclass
from typing import Callable, List
from game import Game, Player

# —————— Data Model ——————
@dataclass
class ChanceCard:
    name: str
    description: str
    action: Callable[['Player', 'Game'], None]

    def apply(self, player: 'Player', game: 'Game') -> None:
        """Execute this card’s effect."""
        self.action(player, game)


# —————— Deck Management ——————
class ChanceDeck:
    def __init__(self, cards: List[ChanceCard]):
        # Work on a copy so the original list stays intact
        self.cards = cards.copy()

    def shuffle_deck(self) -> None:
        random.shuffle(self.cards)

    def draw_card(self) -> ChanceCard:
        card = self.cards.pop(0)
        # “Get Out of Jail Free” isn’t returned to the bottom until used
        if card.name != "GET_OUT_OF_JAIL_FREE":
            self.cards.append(card)
        return card


# —————— Action Functions ——————
def advance_to_go(player, game):
    player.position = 0
    player.balance += 200

def advance_to_illinois(player, game):
    game.move_player_to(player, 24)  # assumes game has a helper
    if player.position < player.last_position:
        player.balance += 200

def advance_to_st_charles(player, game):
    game.move_player_to(player, 11)
    if player.position < player.last_position:
        player.balance += 200

def advance_to_nearest_utility(player, game):
    utility_pos = game.find_nearest(player.position, spaces=game.utilities)
    game.move_player_to(player, utility_pos)
    if not game.is_owned(utility_pos):
        player.offer_purchase(utility_pos)
    else:
        dice_roll = game.roll_dice()
        player.pay_owner(utility_pos, dice_roll * 10)

def advance_to_nearest_railroad(player, game):
    railroad_pos = game.find_nearest(player.position, spaces=game.railroads)
    game.move_player_to(player, railroad_pos)
    if not game.is_owned(railroad_pos):
        player.offer_purchase(railroad_pos)
    else:
        player.pay_owner(railroad_pos, game.rent_for(railroad_pos) * 2)

def bank_dividend(player, game):
    player.balance += 50

def get_out_of_jail_free(player, game):
    player.has_get_out_of_jail_free = True

def go_back_three_spaces(player, game):
    game.move_player_to(player, player.position - 3)

def go_to_jail(player, game):
    game.send_player_to_jail(player)

def general_repairs(player, game):
    cost = player.house_count * 25 + player.hotel_count * 100
    player.balance -= cost

def poor_tax(player, game):
    player.balance -= 15

def trip_to_reading(player, game):
    game.move_player_to(player, 5)
    if player.position < player.last_position:
        player.balance += 200

def walk_on_boardwalk(player, game):
    game.move_player_to(player, 39)

def chairman_of_the_board(player, game):
    for other in game.players:
        if other is not player:
            other.balance += 50
            player.balance  -= 50

def building_loan_matures(player, game):
    player.balance += 150


# —————— Build & Use the Deck ——————
def build_chance_deck() -> ChanceDeck:
    cards = [
        ChanceCard("ADVANCE_TO_GO", "Advance to Go (Collect $200)", advance_to_go),
        ChanceCard("ADVANCE_TO_ILLINOIS", "Advance to Illinois Avenue", advance_to_illinois),
        ChanceCard("ADVANCE_TO_ST_CHARLES", "Advance to St. Charles Place", advance_to_st_charles),
        ChanceCard("ADVANCE_TO_NEAREST_UTILITY", "Advance to Nearest Utility", advance_to_nearest_utility),
        ChanceCard("ADVANCE_TO_NEAREST_RAILROAD", "Advance to Nearest Railroad", advance_to_nearest_railroad),
        ChanceCard("ADVANCE_TO_NEAREST_RAILROAD_2", "Advance to Nearest Railroad (2nd)", advance_to_nearest_railroad),
        ChanceCard("BANK_DIVIDEND", "Bank pays you dividend of $50", bank_dividend),
        ChanceCard("GET_OUT_OF_JAIL_FREE", "Get Out of Jail Free", get_out_of_jail_free),
        ChanceCard("GO_BACK_THREE_SPACES", "Go back three spaces", go_back_three_spaces),
        ChanceCard("GO_TO_JAIL", "Go directly to Jail", go_to_jail),
        ChanceCard("GENERAL_REPAIRS", "Make general repairs on all your property", general_repairs),
        ChanceCard("POOR_TAX", "Pay poor tax of $15", poor_tax),
        ChanceCard("TRIP_TO_READING", "Take a trip to Reading Railroad", trip_to_reading),
        ChanceCard("WALK_ON_BOARDWALK", "Take a walk on Boardwalk", walk_on_boardwalk),
        ChanceCard("CHAIRMAN_OF_THE_BOARD", "Elected Chairman of the Board—Pay each player $50", chairman_of_the_board),
        ChanceCard("BUILDING_LOAN_MATURES", "Your building loan matures—Collect $150", building_loan_matures),
    ]
    deck = ChanceDeck(cards)
    deck.shuffle_deck()
    return deck


# Example of usage inside your game loop:
if __name__ == "__main__":
    # Assume you have a Game and Player classes defined elsewhere:
    from game import Game, Player

    game_controller = Game([...])
    current_player = game_controller.current_player

    chance_deck = build_chance_deck()
    drawn_card = chance_deck.draw_card()
    print(f"You drew: {drawn_card.description}")
    drawn_card.apply(current_player, game_controller)
