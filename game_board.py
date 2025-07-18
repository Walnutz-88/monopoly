from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from dataclasses import dataclass, field, asdict
import redis
from redis.commands.json.path import Path
import json
import ipdb
import subprocess
from properties import RegularProperty, RailroadProperty, UtilityProperty, ChestChanceSpace, SpecialSpace
from dice import Die, DieSet
from player import Player
from chest import ChestDeck, ChestCard
from chance import ChanceDeck, ChanceCard

r = redis.Redis(host="ai.thewcl.com", port=6379, db=3, password="atmega328")
REDIS_KEY = "monopoly:game_state"

# ----------------------------
# Data Model
# Starter class for your game board. Rename and modify for your own game.
# ----------------------------
property_data = {
    "Brown": [
        {
            "name": "Mediterranean Avenue",
            "price": 60,
            "rent": [2, 4, 10, 30, 90, 160, 250],
            "house_cost": 50,
            "position": 1,
        },
        {
            "name": "Baltic Avenue",
            "price": 60,
            "rent": [4, 8, 20, 60, 180, 320, 450],
            "house_cost": 50,
            "position": 3,
        },
    ],
    "Light Blue": [
        {
            "name": "Oriental Avenue",
            "price": 100,
            "rent": [6, 12, 30, 90, 270, 400, 550],
            "house_cost": 50,
            "position": 6,
        },
        {
            "name": "Vermont Avenue",
            "price": 100,
            "rent": [6, 12, 30, 90, 270, 400, 550],
            "house_cost": 50,
            "position": 8,
        },
        {
            "name": "Connecticut Avenue",
            "price": 120,
            "rent": [8, 16, 40, 100, 300, 450, 600],
            "house_cost": 50,
            "position": 9,
        },
    ],
    "Pink": [
        {
            "name": "St. Charles Place",
            "price": 140,
            "rent": [10, 20, 50, 150, 450, 625, 750],
            "house_cost": 100,
            "position": 11,
        },
        {
            "name": "States Avenue",
            "price": 140,
            "rent": [10, 20, 50, 150, 450, 625, 750],
            "house_cost": 100,
            "position": 13,
        },
        {
            "name": "Virginia Avenue",
            "price": 160,
            "rent": [12, 24, 60, 180, 500, 700, 900],
            "house_cost": 100,
            "position": 14,
        },
    ],
    "Orange": [
        {
            "name": "St. James Place",
            "price": 180,
            "rent": [14, 28, 70, 200, 550, 750, 950],
            "house_cost": 100,
            "position": 16,
        },
        {
            "name": "Tennessee Avenue",
            "price": 180,
            "rent": [14, 28, 70, 200, 550, 750, 950],
            "house_cost": 100,
            "position": 18,
        },
        {
            "name": "New York Avenue",
            "price": 200,
            "rent": [16, 32, 80, 220, 600, 800, 1000],
            "house_cost": 100,
            "position": 19,
        },
    ],
    "Red": [
        {
            "name": "Kentucky Avenue",
            "price": 220,
            "rent": [18, 36, 90, 250, 700, 875, 1050],
            "house_cost": 150,
            "position": 21,
        },
        {
            "name": "Indiana Avenue",
            "price": 220,
            "rent": [18, 36, 90, 250, 700, 875, 1050],
            "house_cost": 150,
            "position": 23,
        },
        {
            "name": "Illinois Avenue",
            "price": 240,
            "rent": [20, 40, 100, 300, 750, 925, 1100],
            "house_cost": 150,
            "position": 24,
        },
    ],
    "Yellow": [
        {
            "name": "Atlantic Avenue",
            "price": 260,
            "rent": [22, 44, 110, 330, 800, 975, 1150],
            "house_cost": 150,
            "position": 26,
        },
        {
            "name": "Ventnor Avenue",
            "price": 260,
            "rent": [22, 44, 110, 330, 800, 975, 1150],
            "house_cost": 150,
            "position": 27,
        },
        {
            "name": "Marvin Gardens",
            "price": 280,
            "rent": [24, 48, 120, 360, 850, 1025, 1200],
            "house_cost": 150,
            "position": 29,
        },
    ],
    "Green": [
        {
            "name": "Pacific Avenue",
            "price": 300,
            "rent": [26, 52, 130, 390, 900, 1100, 1275],
            "house_cost": 200,
            "position": 31,
        },
        {
            "name": "North Carolina Avenue",
            "price": 300,
            "rent": [26, 52, 130, 390, 900, 1100, 1275],
            "house_cost": 200,
            "position": 32,
        },
        {
            "name": "Pennsylvania Avenue",
            "price": 320,
            "rent": [28, 56, 150, 450, 1000, 1200, 1400],
            "house_cost": 200,
            "position": 34,
        },
    ],
    "Dark Blue": [
        {
            "name": "Park Place",
            "price": 350,
            "rent": [35, 70, 175, 500, 1100, 1300, 1500],
            "house_cost": 200,
            "position": 37,
        },
        {
            "name": "Boardwalk",
            "price": 400,
            "rent": [50, 100, 200, 600, 1400, 1700, 2000],
            "house_cost": 200,
            "position": 39,
        },
    ],
    "Railroads": [
        {
            "name": "Reading Railroad",
            "price": 200,
            "rent": [25, 50, 100, 200],
            "position": 5,
        },
        {
            "name": "Pennsylvania Railroad",
            "price": 200,
            "rent": [25, 50, 100, 200],
            "position": 15,
        },
        {
            "name": "B. & O. Railroad",
            "price": 200,
            "rent": [25, 50, 100, 200],
            "position": 25,
        },
        {
            "name": "Short Line",
            "price": 200,
            "rent": [25, 50, 100, 200],
            "position": 35,
        },
    ],
    "Utilities": [
        {
            "name": "Electric Company",
            "price": 150,
            "rent": ["4× dice roll", "10× dice roll"],
            "position": 12,
        },
        {
            "name": "Water Works",
            "price": 150,
            "rent": ["4× dice roll", "10× dice roll"],
            "position": 28,
        },
    ],
}
chance_and_chest_spaces = {
    "Chance": [
        {"position": 7},
        {"position": 22},
        {"position": 36},
    ],
    "Community Chest": [
        {"position": 2},
        {"position": 17},
        {"position": 33},
    ],
}
other_spaces = {
    "Corners": [
        {"name": "Go", "position": 0},
        {"name": "Jail / Just Visiting", "position": 10},
        {"name": "Free Parking", "position": 20},
        {"name": "Go To Jail", "position": 30},
    ],
    "Taxes": [
        {"name": "Income Tax", "position": 4},
        {"name": "Luxury Tax", "position": 38},
    ],
}



@dataclass
class MonopolyBoard:
    players: list[Player]
    regular_properties: list[RegularProperty] = field(default_factory=list)
    railroad_properties: list[RailroadProperty] = field(default_factory=list)
    utility_properties: list[UtilityProperty] = field(default_factory=list)
    chance_and_chest_spaces: list[ChestChanceSpace] = field(default_factory=list)
    other_spaces: list[SpecialSpace] = field(default_factory=list)
    state: str = "is_playing"  # is_playing, has_winner, awaiting_purchase_decision
    player_turn: int = 0
    pending_purchase: dict = field(default_factory=dict)  # For storing pending purchase decisions
    chance_deck: ChanceDeck = field(default_factory=ChanceDeck)
    chest_deck: ChestDeck = field(default_factory=ChestDeck)
    
    def is_my_turn(self, player: str) -> bool:
        return self.state == "is_playing" and player == self.players[self.player_turn].name
    
    def check_game_over(self) -> bool:
        """Check if the game is over (only one player left non-bankrupt)."""
        active_players = [p for p in self.players if not p.bankrupt]
        if len(active_players) <= 1:
            self.state = "has_winner"
            return True
        return False
    
    def get_winner(self) -> str:
        """Get the winner's name if game is over."""
        active_players = [p for p in self.players if not p.bankrupt]
        if len(active_players) == 1:
            return active_players[0].name
        return "No winner yet"
    
    def get_space_details(self, position: int) -> dict:
        """Get detailed information about a space based on its position."""
        # Check regular properties
        for prop in self.regular_properties:
            if prop.position == position:
                return {
                    "type": "regular_property",
                    "name": prop.name,
                    "color": prop.color,
                    "buy_price": prop.buy_price,
                    "rent_price": prop.rent_price,
                    "house_hotel_price": prop.house_hotel_price,
                    "owner": prop.owner,
                    "position": prop.position
                }
        
        # Check railroad properties
        for prop in self.railroad_properties:
            if prop.position == position:
                return {
                    "type": "railroad_property",
                    "name": prop.name,
                    "buy_price": prop.buy_price,
                    "rent_price": prop.rent_price,
                    "owner": prop.owner,
                    "position": prop.position
                }
        
        # Check utility properties
        for prop in self.utility_properties:
            if prop.position == position:
                return {
                    "type": "utility_property",
                    "name": prop.name,
                    "buy_price": prop.buy_price,
                    "rent_price": prop.rent_price,
                    "owner": prop.owner,
                    "position": prop.position
                }
        
        # Check chance and community chest spaces
        for space in self.chance_and_chest_spaces:
            if space.position == position:
                return {
                    "type": "chance_chest_space",
                    "name": space.name,
                    "position": space.position,
                    "chance": space.chance,
                    "chest": space.chest
                }
        
        # Check other special spaces
        for space in self.other_spaces:
            if space.position == position:
                return {
                    "type": "special_space",
                    "name": space.name,
                    "position": space.position
                }
        
        # If no space found, return generic position info
        return {
            "type": "unknown",
            "name": f"Position {position}",
            "position": position
        }

    def make_move(self, player: str, index: int) -> dict:
        # Check for game over condition at the beginning of each turn
        if self.check_game_over():
            winner = self.get_winner()
            return {"success": False, "message": f"Game Over! {winner} wins!", "winner": winner}
        
        if self.state != "is_playing":
            return {"success": False, "message": "Game is over. Please reset."}

        if not self.is_my_turn(player):
            return {"success": False, "message": f"It is not {player}'s turn."}
        
        current_player = self.players[self.player_turn]
        
        die_set = DieSet(Die(), Die())
        die1, die2, total_roll, is_doubles = die_set.roll_and_check_doubles()
        
        # Handle jail mechanics
        if current_player.in_jail:
            success, jail_message = current_player.attempt_jail_roll(die1, die2)
            if success:
                # Player got out of jail, can move normally
                current_position, passed_go = current_player.move(total_roll)
                space_details = self.get_space_details(current_position)
                
                # Handle property transactions
                transaction_message = ""
                if space_details["type"] in ["regular_property", "railroad_property", "utility_property"]:
                    transaction_message = self._handle_property_transaction(current_player, space_details)
                
                # Build message with GO passing info
                go_message = " Passed GO! Collected $200." if passed_go else ""
                
                # Check for bankruptcy and game over
                if self.check_game_over():
                    winner = self.get_winner()
                    game_over_message = f" Game Over! {winner} wins!"
                    self.save_to_redis()
                    return {
                        "success": True, 
                        "message": f"{player} rolled ({die1}, {die2}). {jail_message}{go_message} {transaction_message}{game_over_message}", 
                        "board": self.to_dict(),
                        "space_details": space_details,
                        "winner": winner
                    }
                
                # Advance to next player's turn
                self.player_turn = (self.player_turn + 1) % len(self.players)
                
                self.save_to_redis()
                return {
                    "success": True, 
                    "message": f"{player} rolled ({die1}, {die2}). {jail_message}{go_message} {transaction_message}", 
                    "board": self.to_dict(),
                    "space_details": space_details
                }
            else:
                # Player is still in jail
                # Check for bankruptcy and game over (player might have gone bankrupt paying jail fine)
                if self.check_game_over():
                    winner = self.get_winner()
                    game_over_message = f" Game Over! {winner} wins!"
                    self.save_to_redis()
                    return {
                        "success": True, 
                        "message": f"{player} rolled ({die1}, {die2}). {jail_message}{game_over_message}", 
                        "board": self.to_dict(),
                        "space_details": self.get_space_details(10),  # Jail position
                        "winner": winner
                    }
                
                # Advance to next player's turn
                self.player_turn = (self.player_turn + 1) % len(self.players)
                
                self.save_to_redis()
                return {
                    "success": True, 
                    "message": f"{player} rolled ({die1}, {die2}). {jail_message}", 
                    "board": self.to_dict(),
                    "space_details": self.get_space_details(10)  # Jail position
                }
        
        # Normal move (player not in jail)
        current_position, passed_go = current_player.move(total_roll)
        space_details = self.get_space_details(current_position)
        
        # Handle different types of spaces
        transaction_message = ""
        
        if space_details["type"] == "special_space":
            # Handle special spaces (Go, Jail, Free Parking, Go To Jail, taxes)
            transaction_message = self._handle_special_space(current_player, space_details, total_roll)
            
            # If player was sent to jail, update position and space details
            if space_details["name"] == "Go To Jail":
                current_position = current_player.position
                space_details = self.get_space_details(current_position)
                
        elif space_details["type"] == "chance_chest_space":
            # Handle Chance and Community Chest spaces
            transaction_message = self._handle_chance_and_chest_spaces(current_player, space_details)
            
        elif space_details["type"] in ["regular_property", "railroad_property", "utility_property"]:
            # Handle property transactions
            if space_details["type"] == "utility_property" and space_details["owner"] is not None and space_details["owner"] != current_player.name:
                # For utilities, use actual dice roll for rent calculation
                rent_amount = self._calculate_utility_rent(space_details, total_roll)
                current_player.pay(rent_amount)
                
                # Find the owner and pay them rent
                for player_obj in self.players:
                    if player_obj.name == space_details["owner"]:
                        player_obj.receive(rent_amount)
                        break
                
                transaction_message = f"Paid ${rent_amount} rent to {space_details['owner']} for {space_details['name']} (dice roll: {total_roll})."
            else:
                transaction_message = self._handle_property_transaction(current_player, space_details)
        
        # Build message with GO passing info
        go_message = " Passed GO! Collected $200." if passed_go else ""
        
        # Check for bankruptcy and game over
        if self.check_game_over():
            winner = self.get_winner()
            game_over_message = f" Game Over! {winner} wins!"
            self.save_to_redis()
            return {
                "success": True, 
                "message": f"{player} rolled ({die1}, {die2}) = {total_roll} and moved to position {current_position}.{go_message} {transaction_message}{game_over_message}", 
                "board": self.to_dict(),
                "space_details": space_details,
                "winner": winner
            }
        
        # Advance to next player's turn
        self.player_turn = (self.player_turn + 1) % len(self.players)
        
        self.save_to_redis()
        return {
            "success": True, 
            "message": f"{player} rolled ({die1}, {die2}) = {total_roll} and moved to position {current_position}.{go_message} {transaction_message}", 
            "board": self.to_dict(),
            "space_details": space_details
        }
    def _handle_property_transaction(self, current_player: Player, space_details: dict) -> str:
        """Handle property buying or rent payment when a player lands on a property."""
        property_name = space_details["name"]
        owner = space_details["owner"]
        
        # If property is unowned, indicate that a purchase decision is needed
        if owner is None:
            buy_price = space_details["buy_price"]
            # Only prompt for purchase if buy_price > 0 to avoid zero cost properties
            if buy_price > 0:
                if current_player.money >= buy_price:
                    return f"Can buy {property_name} for ${buy_price}."
                else:
                    return f"Cannot afford {property_name} (${buy_price})."
            else:
                return f"Landed on {property_name} (no purchase required)."
            
        # If property is owned by another player, pay rent
        elif owner != current_player.name:
            rent_amount = self._calculate_rent(space_details)
            current_player.pay(rent_amount)
            
            # Find the owner and pay them rent
            for player in self.players:
                if player.name == owner:
                    player.receive(rent_amount)
                    break
            
            return f"Paid ${rent_amount} rent to {owner} for {property_name}."
        
        # Player owns the property
        else:
            return f"Landed on own property: {property_name}."
    
    def handle_property_purchase(self, player_name: str, property_position: int, decision: str) -> dict:
        """Handle a property purchase decision made by a player."""
        # Find the player
        player = None
        for p in self.players:
            if p.name == player_name:
                player = p
                break
        
        if not player:
            return {"success": False, "message": "Player not found"}
        
        # Get space details
        space_details = self.get_space_details(property_position)
        
        if space_details["owner"] is not None:
            return {"success": False, "message": "Property is already owned"}
        
        if decision.lower() == 'y':
            buy_price = space_details["buy_price"]
            if player.money >= buy_price:
                player.pay(buy_price)
                self._set_property_owner(space_details, player_name)
                self.save_to_redis()
                print(f"{player_name} bought {space_details['name']} for ${buy_price}")
                return {"success": True, "message": f"Bought {space_details['name']} for ${buy_price}"}
            else:
                return {"success": False, "message": "Insufficient funds"}
        else:
            print(f"{player_name} chose not to buy {space_details['name']}")
            return {"success": True, "message": f"Chose not to buy {space_details['name']}"}
    
    def _simulate_property_purchase_choice(self, player_name: str, property_name: str, buy_price: int) -> str:
        """Store purchase decision state and return 'pending' to indicate waiting for user input."""
        print(f"\n{player_name}, would you like to buy {property_name} for ${buy_price}? (y/n)")
        
        # Store the pending purchase decision in the board state
        self.pending_purchase = {
            "player": player_name,
            "property": property_name,
            "price": buy_price,
            "position": self.players[self.player_turn].position
        }
        self.state = "awaiting_purchase_decision"
        
        print(f"Waiting for {player_name} to make a purchase decision...")
        return "pending"
    
    def _set_property_owner(self, space_details: dict, owner_name: str):
        """Set the owner of a property based on its type and position."""
        position = space_details["position"]
        
        if space_details["type"] == "regular_property":
            for prop in self.regular_properties:
                if prop.position == position:
                    prop.owner = owner_name
                    break
        elif space_details["type"] == "railroad_property":
            for prop in self.railroad_properties:
                if prop.position == position:
                    prop.owner = owner_name
                    break
        elif space_details["type"] == "utility_property":
            for prop in self.utility_properties:
                if prop.position == position:
                    prop.owner = owner_name
                    break
    
    def _calculate_rent(self, space_details: dict) -> int:
        """Calculate rent for a property based on its type and ownership."""
        if space_details["type"] == "regular_property":
            # For regular properties, rent is based on house count (index 0 for no houses)
            rent_prices = space_details["rent_price"]
            owner = space_details["owner"]
            color = space_details["color"]
            
            # Check if owner has monopoly (owns all properties in this color group)
            properties_in_color = [prop for prop in self.regular_properties if prop.color == color]
            owned_properties_in_color = [prop for prop in properties_in_color if prop.owner == owner]
            
            # Get house count for this specific property
            house_count = 0
            for prop in self.regular_properties:
                if prop.position == space_details["position"]:
                    house_count = prop.house_count
                    break
            
            # If owner has monopoly, calculate rent based on house count
            if len(owned_properties_in_color) == len(properties_in_color):
                if house_count == 0:
                    return rent_prices[1]  # Set rent for monopoly with no houses (index 1)
                elif house_count <= 4:
                    return rent_prices[house_count + 1]  # Rent for 1-4 houses (indices 2-5)
                else:  # house_count == 5 (hotel)
                    return rent_prices[6]  # Rent for hotel (index 6)
            else:
                return rent_prices[0]  # Basic rent with no monopoly (index 0)
        
        elif space_details["type"] == "railroad_property":
            # For railroads, rent depends on how many railroads the owner has
            owner = space_details["owner"]
            railroads_owned = sum(1 for prop in self.railroad_properties if prop.owner == owner)
            rent_prices = space_details["rent_price"]
            # Rent index: 0 for 1 railroad, 1 for 2 railroads, etc.
            return rent_prices[min(railroads_owned - 1, len(rent_prices) - 1)]
        
        elif space_details["type"] == "utility_property":
            # For utilities, rent is based on dice roll multiplier
            owner = space_details["owner"]
            utilities_owned = sum(1 for prop in self.utility_properties if prop.owner == owner)
            rent_multiplier = space_details["rent_price"]
            
            # If owner has 1 utility, multiply dice roll by 4; if 2 utilities, multiply by 10
            multiplier = rent_multiplier[0] if utilities_owned == 1 else rent_multiplier[1]
            
            # For simplicity, assume a dice roll of 7 (average)
            # In a real game, you'd use the actual dice roll
            return 7 * multiplier
        
        return 0
    
    def get_monopoly_sets(self, player_name: str) -> list[dict]:
        """Get all monopoly sets owned by a player."""
        monopoly_sets = []
        
        # Group properties by color
        color_groups = {}
        for prop in self.regular_properties:
            if prop.color not in color_groups:
                color_groups[prop.color] = []
            color_groups[prop.color].append(prop)
        
        # Check each color group for monopoly
        for color, properties in color_groups.items():
            owned_properties = [prop for prop in properties if prop.owner == player_name]
            if len(owned_properties) == len(properties):  # Player owns all properties in this color
                monopoly_sets.append({
                    "color": color,
                    "properties": owned_properties
                })
        
        return monopoly_sets
    
    def can_buy_houses(self, player_name: str, property_position: int) -> tuple[bool, str]:
        """Check if a player can buy a house on a specific property."""
        # Find the property
        target_property = None
        for prop in self.regular_properties:
            if prop.position == property_position:
                target_property = prop
                break
        
        if not target_property:
            return False, "Property not found"
        
        if target_property.owner != player_name:
            return False, "You don't own this property"
        
        # Check if player has monopoly
        monopoly_sets = self.get_monopoly_sets(player_name)
        player_monopoly = None
        for monopoly_set in monopoly_sets:
            if target_property in monopoly_set["properties"]:
                player_monopoly = monopoly_set
                break
        
        if not player_monopoly:
            return False, "You must own all properties in the color group to buy houses"
        
        # Check if property already has a hotel
        if target_property.house_count >= 5:
            return False, "Property already has a hotel"
        
        # Check even building rule (can't have more than 1 house difference)
        min_houses = min(prop.house_count for prop in player_monopoly["properties"])
        if target_property.house_count > min_houses:
            return False, "Must build evenly across the monopoly set"
        
        # Check if player has enough money
        house_cost = target_property.house_hotel_price
        player = next(p for p in self.players if p.name == player_name)
        if player.money < house_cost:
            return False, f"Insufficient funds. Need ${house_cost}"
        
        return True, "Can buy house"
    
    def buy_house(self, player_name: str, property_position: int) -> dict:
        """Buy a house on a specific property."""
        can_buy, message = self.can_buy_houses(player_name, property_position)
        
        if not can_buy:
            return {"success": False, "message": message}
        
        # Find the property and player
        target_property = None
        for prop in self.regular_properties:
            if prop.position == property_position:
                target_property = prop
                break
        
        player = next(p for p in self.players if p.name == player_name)
        
        # Buy the house
        house_cost = target_property.house_hotel_price
        player.pay(house_cost)
        target_property.house_count += 1
        
        # Save to Redis
        self.save_to_redis()
        
        if target_property.house_count == 5:
            return {"success": True, "message": f"Bought hotel on {target_property.name} for ${house_cost}"}
        else:
            return {"success": True, "message": f"Bought house on {target_property.name} for ${house_cost}"}
    
    def get_house_buying_options(self, player_name: str) -> list[dict]:
        """Get all properties where a player can buy houses."""
        options = []
        monopoly_sets = self.get_monopoly_sets(player_name)
        
        for monopoly_set in monopoly_sets:
            for prop in monopoly_set["properties"]:
                can_buy, message = self.can_buy_houses(player_name, prop.position)
                if can_buy:
                    house_word = "hotel" if prop.house_count == 4 else "house"
                    options.append({
                        "position": prop.position,
                        "name": prop.name,
                        "color": prop.color,
                        "house_count": prop.house_count,
                        "house_cost": prop.house_hotel_price,
                        "description": f"{prop.name} ({prop.house_count} houses) - ${prop.house_hotel_price} for {house_word}"
                    })
        
        return options
    
    def _handle_special_space(self, current_player: Player, space_details: dict, dice_roll: int) -> str:
        """Handle landing on special spaces like Go, Jail, Free Parking, Go To Jail, and taxes."""
        space_name = space_details["name"]
        
        if space_name == "Go":
            # Player lands on Go - they already collected $200 for passing/landing on Go
            # No additional money is collected for landing on Go
            return "Landed on Go! Already collected $200 for passing Go."
        
        elif space_name == "Jail / Just Visiting":
            # Player is just visiting jail, no action needed
            return "Just visiting jail."
        
        elif space_name == "Free Parking":
            # Free Parking - nothing happens in standard Monopoly
            return "Free parking! Nothing happens."
        
        elif space_name == "Go To Jail":
            # Send player to jail
            current_player.go_to_jail()
            return "Go to jail! Do not pass Go, do not collect $200."
        
        elif space_name == "Income Tax":
            # Income Tax - pay $200 or 10% of net worth (whichever is less)
            net_worth = current_player.net_worth()
            tax_amount = min(200, net_worth // 10)  # 10% of net worth or $200, whichever is less
            
            if current_player.pay(tax_amount):
                return f"Income Tax! Paid ${tax_amount}."
            else:
                return f"Income Tax! Player went bankrupt trying to pay ${tax_amount}."
        
        elif space_name == "Luxury Tax":
            # Luxury Tax - pay $75 (in classic Monopoly it's $75)
            if current_player.pay(75):
                return "Luxury Tax! Paid $75."
            else:
                return "Luxury Tax! Player went bankrupt trying to pay $75."
        
        return f"Landed on {space_name}."
    
    def _handle_chance_and_chest_spaces(self, current_player: Player, space_details: dict) -> str:
        """Handle landing on Chance and Community Chest spaces."""
        space_name = space_details["name"]
        
        if space_name == "Chance":
            # Draw a Chance card
            card, keep_card = self.chance_deck.draw_card()
            
            # If it's a "Get Out of Jail Free" card, add it to the player's collection
            if keep_card:
                current_player.get_out_of_jail_free += 1
                return f"Landed on Chance! Drew: {card.description}. Card kept for future use."
            else:
                # Execute the card's action
                self._execute_chance_action(card.action, current_player)
                return f"Landed on Chance! Drew: {card.description}."
        
        elif space_name == "Community Chest":
            # Draw a Community Chest card
            card, keep_card = self.chest_deck.draw_card()
            
            # If it's a "Get Out of Jail Free" card, add it to the player's collection
            if keep_card:
                current_player.get_out_of_jail_free += 1
                return f"Landed on Community Chest! Drew: {card.description}. Card kept for future use."
            else:
                # Execute the card's action
                self._execute_chest_action(card.action, current_player)
                return f"Landed on Community Chest! Drew: {card.description}."
        
        return f"Landed on {space_name}."
    
    def _calculate_utility_rent(self, space_details: dict, dice_roll: int) -> int:
        """Calculate rent for utilities based on actual dice roll."""
        owner = space_details["owner"]
        utilities_owned = sum(1 for prop in self.utility_properties if prop.owner == owner)
        
        # If owner has 1 utility, multiply dice roll by 4; if 2 utilities, multiply by 10
        multiplier = 4 if utilities_owned == 1 else 10
        return dice_roll * multiplier
    
    def _execute_chance_action(self, action: str, player: Player):
        """Execute a chance card action based on the action string."""
        if action == "advance_to_go":
            player.position = 0
            player.receive(200)
        elif action == "bank_dividend":
            player.receive(50)
        elif action == "poor_tax":
            player.pay(15)
        elif action == "building_loan_matures":
            player.receive(150)
        elif action == "go_to_jail":
            player.go_to_jail()
        elif action == "chairman_of_the_board":
            # Pay each other player $50
            for other_player in self.players:
                if other_player != player:
                    other_player.receive(50)
                    player.pay(50)
        elif action == "general_repairs":
            # Pay $25 per house and $100 per hotel
            # This is a simplified implementation - in a full game you'd track houses/hotels
            repair_cost = 0  # Would calculate based on actual properties owned
            player.pay(repair_cost)
        elif action == "go_back_three_spaces":
            new_position = (player.position - 3) % 40
            player.position = new_position
        # Add more chance card actions as needed
        else:
            # For actions not implemented yet, just log it
            print(f"Chance action '{action}' not implemented yet")
    
    def _execute_chest_action(self, action: str, player: Player):
        """Execute a community chest card action based on the action string."""
        if action == "advance_to_go":
            player.position = 0
            player.receive(200)
        elif action == "bank_error":
            player.receive(200)
        elif action == "doctor_fees":
            player.pay(50)
        elif action == "sale_of_stock":
            player.receive(50)
        elif action == "go_to_jail":
            player.go_to_jail()
        elif action == "opera_night":
            # Collect $50 from every other player
            for other_player in self.players:
                if other_player != player:
                    other_player.pay(50)
                    player.receive(50)
        elif action == "holiday_fund":
            player.receive(100)
        elif action == "income_tax_refund":
            player.receive(20)
        elif action == "birthday":
            # Collect $10 from every other player
            for other_player in self.players:
                if other_player != player:
                    other_player.pay(10)
                    player.receive(10)
        elif action == "life_insurance_matures":
            player.receive(100)
        elif action == "hospital_fees":
            player.pay(100)
        elif action == "school_fees":
            player.pay(150)
        elif action == "consultancy_fee":
            player.receive(25)
        elif action == "street_repairs":
            # Pay $40 per house and $115 per hotel
            # This is a simplified implementation - in a full game you'd track houses/hotels
            repair_cost = 0  # Would calculate based on actual properties owned
            player.pay(repair_cost)
        elif action == "beauty_contest":
            player.receive(10)
        # Add more chest card actions as needed
        else:
            # For actions not implemented yet, just log it
            print(f"Chest action '{action}' not implemented yet")
    
    def reset(self, new_players: list[str]):
        self.state = "is_playing"
        self.players = [Player(name=name, token=f"token_{i+1}") for i, name in enumerate(new_players)]
        self.player_turn = 0
        self.regular_properties = []
        self.railroad_properties = []
        self.utility_properties = []
        self.chance_and_chest_spaces = []
        self.other_spaces = []
        for group, names in property_data.items():
            if group == "Railroads":
                for prop_data in names:
                    prop = RailroadProperty(
                        name=prop_data["name"],
                        buy_price=prop_data["price"],
                        rent_price=[25, 50, 100, 200],
                        owner=None,
                        position=prop_data["position"],
                    )
                    self.railroad_properties.append(prop)
            elif group == "Utilities":
                for prop_data in names:
                    prop = UtilityProperty(
                        name=prop_data["name"],
                        buy_price=prop_data["price"],
                        rent_price=[4, 10],
                        owner=None,
                        position=prop_data["position"],
                    )
                    self.utility_properties.append(prop)
            else:
                for prop_data in names:
                    prop = RegularProperty(
                        name=prop_data["name"],
                        color=group,
                        buy_price=prop_data["price"],
                        rent_price=prop_data["rent"],
                        house_hotel_price=prop_data["house_cost"],
                        owner=None,
                        position=prop_data["position"],
                    )
                    self.regular_properties.append(prop)
        
        for group, names in chance_and_chest_spaces.items():
            if group == "Chance":
                for prop_data in names:
                    prop = ChestChanceSpace(
                        name="Chance",
                        position=prop_data["position"],
                        chance=True,
                        chest=False,
                    )
                    self.chance_and_chest_spaces.append(prop)
            elif group == "Community Chest":
                for prop_data in names:
                    prop = ChestChanceSpace(
                        name="Community Chest",
                        position=prop_data["position"],
                        chest=True,
                        chance=False,
                    )
                    self.chance_and_chest_spaces.append(prop)
        
        for group, names in other_spaces.items():
            for prop_data in names:
                prop = SpecialSpace(
                    name=prop_data["name"],
                    position=prop_data["position"],
                )
                self.other_spaces.append(prop)
        
        # Shuffle the chance and chest decks to randomize card order
        self.chance_deck.shuffle_deck()
        self.chest_deck.shuffle_deck()
        
        self.save_to_redis()

    def save_to_redis(self):
        r.json().set(REDIS_KEY, Path.root_path(), self.to_dict())

    @classmethod
    def load_from_redis(cls):
        data = r.json().get(REDIS_KEY)
        if not data:
            return cls(players=[])
        
        # Convert player dictionaries back to Player objects
        players = [Player(**player_data) for player_data in data.get('players', [])]
        
        # Convert property dictionaries back to property objects
        regular_properties = [RegularProperty(**prop_data) for prop_data in data.get('regular_properties', [])]
        railroad_properties = [RailroadProperty(**prop_data) for prop_data in data.get('railroad_properties', [])]
        utility_properties = [UtilityProperty(**prop_data) for prop_data in data.get('utility_properties', [])]
        chance_and_chest_spaces = [ChestChanceSpace(**prop_data) for prop_data in data.get('chance_and_chest_spaces', [])]
        other_spaces = [SpecialSpace(**prop_data) for prop_data in data.get('other_spaces', [])]
        
        # Deserialize deck states
        chance_deck = ChanceDeck.from_dict(data.get('chance_deck', {})) if data.get('chance_deck') else ChanceDeck()
        chest_deck = ChestDeck.from_dict(data.get('chest_deck', {})) if data.get('chest_deck') else ChestDeck()
        
        return cls(
            players=players,
            regular_properties=regular_properties,
            railroad_properties=railroad_properties,
            utility_properties=utility_properties,
            chance_and_chest_spaces=chance_and_chest_spaces,
            other_spaces=other_spaces,
            state=data.get('state', 'is_playing'),
            player_turn=data.get('player_turn', 0),
            pending_purchase=data.get('pending_purchase', {}),
            chance_deck=chance_deck,
            chest_deck=chest_deck
        )

    def to_dict(self):
        result = asdict(self)
        # Serialize deck states
        result['chance_deck'] = self.chance_deck.to_dict()
        result['chest_deck'] = self.chest_deck.to_dict()
        return result

    def serialize(self):
        return json.dumps(self.to_dict())


# ----------------------------
# FastAPI App
# ----------------------------

app = FastAPI()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove broken connections
                self.active_connections.remove(connection)

manager = ConnectionManager()


class MoveRequest(BaseModel):
    player: str
    index: int


@app.get("/state")
def get_state():
    board = MonopolyBoard.load_from_redis()
    return board.to_dict()


@app.post("/move")
def post_move(req: MoveRequest):
    board = MonopolyBoard.load_from_redis()
    # ipdb.set_trace()
    result = board.make_move(req.player, req.index)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result




class PurchaseDecisionRequest(BaseModel):
    player: str
    position: int
    decision: str  # 'y' or 'n'


@app.post("/purchase")
def post_purchase_decision(req: PurchaseDecisionRequest):
    board = MonopolyBoard.load_from_redis()
    result = board.handle_property_purchase(req.player, req.position, req.decision)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


class JailActionRequest(BaseModel):
    player: str
    action: str  # 'use_card' or 'pay_fine'

@app.post("/jail_action")
def post_jail_action(req: JailActionRequest):
    board = MonopolyBoard.load_from_redis()
    
    # Find the player
    player = None
    for p in board.players:
        if p.name == req.player:
            player = p
            break
    
    if not player:
        raise HTTPException(status_code=400, detail="Player not found")
    
    if not player.in_jail:
        raise HTTPException(status_code=400, detail="Player is not in jail")
    
    if req.action == "use_card":
        success = player.use_get_out_of_jail_free_card()
        if success:
            board.save_to_redis()
            return {"success": True, "message": f"{req.player} used a Get Out of Jail Free card!"}
        else:
            return {"success": False, "message": "No Get Out of Jail Free cards available"}
    
    elif req.action == "pay_fine":
        success = player.pay_jail_fine()
        if success:
            board.save_to_redis()
            return {"success": True, "message": f"{req.player} paid $50 fine and got out of jail!"}
        else:
            return {"success": False, "message": "Insufficient funds to pay jail fine"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'use_card' or 'pay_fine'")

class ResetRequest(BaseModel):
    num_players: int

@app.post("/reset")
def post_reset(req: ResetRequest):
    # Validate number of players
    if not (2 <= req.num_players <= 6):
        raise HTTPException(status_code=400, detail="Number of players must be between 2 and 6")
    
    num_players = req.num_players
    
    # Create the specified number of players
    player_names = [f"Player {i+1}" for i in range(num_players)]
    players = [Player(name=name, token=f"token_{i+1}") for i, name in enumerate(player_names)]
    
    # Create board and reset with the new players
    board = MonopolyBoard(players)
    board.reset(player_names)
    
    return {"success": True, "message": f"Game reset with {num_players} players", "players": player_names}


class HousePurchaseRequest(BaseModel):
    player: str
    position: int

@app.post("/buy_house")
def post_buy_house(req: HousePurchaseRequest):
    board = MonopolyBoard.load_from_redis()
    result = board.buy_house(req.player, req.position)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@app.get("/house_options/{player}")
def get_house_options(player: str):
    board = MonopolyBoard.load_from_redis()
    options = board.get_house_buying_options(player)
    return {"options": options}

@app.get("/monopolies/{player}")
def get_monopolies(player: str):
    board = MonopolyBoard.load_from_redis()
    monopolies = board.get_monopoly_sets(player)
    return {"monopolies": monopolies}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
