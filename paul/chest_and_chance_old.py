from dataclasses import dataclass
import random

community_chest_cards = [
    "Advance to Go (Collect $200)",
    "Bank error in your favor—Collect $200",
    "Doctor's fee—Pay $50",
    "From sale of stock you get $50",
    "Get Out of Jail Free",
    "Go to Jail–Go directly to jail–Do not pass Go–Do not collect $200",
    "Grand Opera Night—Collect $50 from every player for opening night seats",
    "Holiday Fund matures—Receive $100",
    "Income tax refund–Collect $20",
    "It is your birthday—Collect $10",
    "Life insurance matures–Collect $100",
    "Pay hospital fees of $100",
    "Pay school fees of $50",
    "Receive $25 consultancy fee",
    "You are assessed for street repairs–Pay $40 per house–$115 per hotel",
    "You have won second prize in a beauty contest–Collect $10",
    "You inherit $100"
]
chance_cards = [
    "Advance to Go (Collect $200)",
    "Advance to Illinois Ave—If you pass Go, collect $200",
    "Advance to St. Charles Place – If you pass Go, collect $200",
    "Advance token to nearest Utility. If unowned, you may buy it from the Bank. If owned, throw dice and pay owner a total ten times the amount thrown.",
    "Advance token to the nearest Railroad and pay owner twice the rental to which he/she is otherwise entitled. If Railroad is unowned, you may buy it from the Bank.",
    "Bank pays you dividend of $50",
    "Get Out of Jail Free",
    "Go Back 3 Spaces",
    "Go to Jail–Go directly to Jail–Do not pass Go–Do not collect $200",
    "Make general repairs on all your property–For each house pay $25–For each hotel $100",
    "Pay poor tax of $15",
    "Take a trip to Reading Railroad–If you pass Go, collect $200",
    "Take a walk on the Boardwalk–Advance token to Boardwalk",
    "You have been elected Chairman of the Board–Pay each player $50",
    "Your building and loan matures—Collect $150",
    "You have won a crossword competition—Collect $100"
]


@dataclass
class ChestAndChanceDeck:
    
    def draw_chest_card(self):
        ''' Returns a random card from the chest deck '''
        return random.choice(community_chest_cards)
    
    def draw_chance_card(self):
        ''' Returns a random card from the chance deck '''
        return random.choice(chance_cards)