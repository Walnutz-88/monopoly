import random
from dataclasses import dataclass, field
from typing import List
#from game import Game, Player

# —————— Data Model ——————
@dataclass
class ChestCard:
    name: str
    description: str
    action: str


def build_chest_deck() -> List[ChestCard]:
    return [
        ChestCard("ADVANCE_TO_GO", "Advance to Go (Collect $200)", "advance_to_go"),
        ChestCard("BANK_ERROR_IN_YOUR_FAVOR", "Bank error in your favor — Collect $200", "bank_error"),
        ChestCard("DOCTOR_FEES", "Doctor’s fees — Pay $50", "doctor_fees"),
        ChestCard("SALE_OF_STOCK", "From sale of stock you get $50", "sale_of_stock"),
        ChestCard("GET_OUT_OF_JAIL_FREE", "Get Out of Jail Free — This card may be kept until needed", "get_out_of_jail_free"),
        ChestCard("GO_TO_JAIL", "Go to Jail — Go directly to jail", "go_to_jail"),
        ChestCard("OPERA_NIGHT", "Grand Opera Night — Collect $50 from every player", "opera_night"),
        ChestCard("HOLIDAY_FUND_MATURES", "Holiday Fund matures — Receive $100", "holiday_fund"),
        ChestCard("INCOME_TAX_REFUND", "Income tax refund — Collect $20", "income_tax_refund"),
        ChestCard("BIRTHDAY", "It’s your birthday — Collect $10 from every player", "birthday"),
        ChestCard("LIFE_INSURANCE_MATURES", "Life insurance matures — Collect $100", "life_insurance_matures"),
        ChestCard("HOSPITAL_FEES", "Pay hospital fees of $100", "hospital_fees"),
        ChestCard("SCHOOL_FEES", "Pay school fees of $150", "school_fees"),
        ChestCard("CONSULTANCY_FEE", "Receive $25 consultancy fee", "consultancy_fee"),
        ChestCard("STREET_REPAIRS", "You are assessed for street repairs: $40/house, $115/hotel", "street_repairs"),
        ChestCard("BEAUTY_CONTEST", "You have won second prize in a beauty contest — Collect $10", "beauty_contest"),
    ]
    

# —————— Deck Management ——————
@dataclass
class ChestDeck:
    cards: List[ChestCard] = field(default_factory=build_chest_deck)

    
    def shuffle_deck(self) -> None:
        random.shuffle(self.cards)

    def draw_card(self) -> tuple[ChestCard, bool]:
        """Draw a card from the deck. Returns (card, keep_card)"""
        card = self.cards.pop(0)
        keep_card = card.name == "GET_OUT_OF_JAIL_FREE"
        
        if not keep_card:
            self.cards.append(card)
        
        return card, keep_card
    
    def to_dict(self) -> dict:
        """Convert deck to dictionary for serialization."""
        return {
            "cards": [{
                "name": card.name,
                "description": card.description,
                "action": card.action
            } for card in self.cards]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChestDeck':
        """Create deck from dictionary."""
        cards = [ChestCard(
            name=card_data["name"],
            description=card_data["description"],
            action=card_data["action"]
        ) for card_data in data.get("cards", [])]
        
        # If no cards data, create default deck
        if not cards:
            cards = build_chest_deck()
        
        return cls(cards=cards)


# —————— Action Functions ——————

def bank_error(player, game):
    player.balance += 200

def doctor_fees(player, game):
    player.balance -= 50

def sale_of_stock(player, game):
    player.balance += 50

def get_out_of_jail_free(player, game):
    player.has_get_out_of_jail_free = True

def go_to_jail(player, game):
    game.send_player_to_jail(player)

def opera_night(player, game):
    for other in game.players:
        if other is not player:
            other.balance -= 50
            player.balance += 50

def holiday_fund(player, game):
    player.balance += 100

def income_tax_refund(player, game):
    player.balance += 20

def birthday(player, game):
    for other in game.players:
        if other is not player:
            other.balance -= 10
            player.balance += 10

def life_insurance_matures(player, game):
    player.balance += 100

def hospital_fees(player, game):
    player.balance -= 100

def school_fees(player, game):
    player.balance -= 150

def consultancy_fee(player, game):
    player.balance += 25

def street_repairs(player, game):
    cost = player.house_count * 40 + player.hotel_count * 115
    player.balance -= cost

def beauty_contest(player, game):
    player.balance += 10

# —————— Build & Use the Deck ——————
# Example of usage inside your game loop:
if __name__ == "__main__":
    deck = ChestDeck()
    deck.shuffle_deck()

    # Simulate landing on a Chance tile
    drawn_card = deck.draw_card()
    print(f"You drew: {drawn_card.name} — {drawn_card.description}")
    