from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dataclasses import dataclass, field, asdict
import redis
from redis.commands.json.path import Path
import json
import ipdb
from properties import RegularProperty, RailroadProperty, UtilityProperty
from dice import Die, DieSet
from Jiayi.player import Player

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


@dataclass
class MonopolyBoard:
    players: list[Player]
    regular_properties: list[RegularProperty] = field(default_factory=list)
    railroad_properties: list[RailroadProperty] = field(default_factory=list)
    utility_properties: list[UtilityProperty] = field(default_factory=list)
    state: str = "is_playing"  # is_playing, has_winner
    player_turn: int = 0
    
    def is_my_turn(self, player: str) -> bool:
        return self.state == "is_playing" and player == self.players[self.player_turn].name

    def make_move(self, player: str, index: int) -> dict:
        if self.state != "is_playing":
            return {"success": False, "message": "Game is over. Please reset."}

        if not self.is_my_turn(player):
            return {"success": False, "message": f"It is not {player}'s turn."} 
        
        print (f"{player} is rolling the dice...")
        print (f"{player} is on {self.players[self.player_turn].position}.")
        die_set = DieSet(Die(), Die())
        roll = die_set.roll_twice()
        self.players[self.player_turn].move(roll[2])
        print (f"{player} rolled a {roll[2]}.")
        print (f"{player} is now on {self.players[self.player_turn].position}.")
        
        # Advance to next player's turn
        self.player_turn = (self.player_turn + 1) % len(self.players)
        
        self.save_to_redis()
        return {"success": True, "message": f"{player} rolled {roll[2]} and moved to position {self.players[(self.player_turn - 1) % len(self.players)].position}.", "board": self.to_dict()}
    
    def reset(self, new_players: list[str]):
        self.state = "is_playing"
        self.players = [Player(name=name, token=f"token_{i+1}") for i, name in enumerate(new_players)]
        self.player_turn = 0
        self.regular_properties = []
        self.railroad_properties = []
        self.utility_properties = []
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
        
        return cls(
            players=players,
            regular_properties=regular_properties,
            railroad_properties=railroad_properties,
            utility_properties=utility_properties,
            state=data.get('state', 'is_playing'),
            player_turn=data.get('player_turn', 0)
        )

    def to_dict(self):
        return asdict(self)

    def serialize(self):
        return json.dumps(self.to_dict())


# ----------------------------
# FastAPI App
# ----------------------------

app = FastAPI()


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


@app.post("/reset")
def post_reset():
    player1 = Player(name="Player 1", token="token_1")
    player2 = Player(name="Player 2", token="token_2")
    board = MonopolyBoard([player1, player2])
    board.reset(["Player 1", "Player 2"])
    return {"message": "Game reset", "board": board.to_dict()}
