'''
ai_player.py

Defines the AIPlayer class that extends Player to use ChatGPT for decision making.
'''

import json
import os
import requests
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from player import Player


@dataclass
class GameState:
    """Represents the current game state for AI decision making."""
    current_player: str
    board_position: int
    money: int
    properties: List[str]
    other_players: List[Dict[str, Any]]
    available_properties: List[Dict[str, Any]]
    dice_roll: Optional[Tuple[int, int]] = None
    turn_phase: str = "move"  # "move", "buy", "trade", "jail"
    special_situation: Optional[str] = None


class AIPlayer(Player):
    """
    AI Player that uses ChatGPT to make decisions through the ai.thewcl.com server.
    """
    
    def __init__(self, name: str, token: str, api_key: Optional[str] = None, 
                 server_url: str = "http://ai.thewcl.com:6502"):
        super().__init__(name, token)
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.server_url = server_url
        self.is_ai = True
        self.decision_history = []
        
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided via parameter or OPENAI_API_KEY environment variable")
    
    def _make_api_request(self, prompt: str, system_prompt: str = None) -> str:
        """
        Make a request to the ChatGPT API through the ai.thewcl.com server.
        
        Args:
            prompt: The user prompt for ChatGPT
            system_prompt: Optional system prompt to set context
            
        Returns:
            str: The AI's response
        """
        try:
            payload = {
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt or "You are an AI playing Monopoly. Make strategic decisions based on the game state."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 300,
                "temperature": 0.7,
                "api_key": self.api_key
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.post(
                f"{self.server_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return "I need to think about this more carefully."
                
        except Exception as e:
            print(f"Error making API request: {e}")
            return "I'll make a conservative choice."
    
    def _format_game_state(self, game_state: GameState) -> str:
        """Format game state into a readable prompt for ChatGPT."""
        prompt = f"""
MONOPOLY GAME STATE:
Current Player: {game_state.current_player}
Position: {game_state.board_position}
Money: ${game_state.money}
Properties Owned: {', '.join(game_state.properties) if game_state.properties else 'None'}
Turn Phase: {game_state.turn_phase}

OTHER PLAYERS:
"""
        for player in game_state.other_players:
            prompt += f"- {player['name']}: ${player['money']}, {len(player['properties'])} properties\n"
        
        if game_state.available_properties:
            prompt += "\nAVAILABLE PROPERTIES:\n"
            for prop in game_state.available_properties:
                prompt += f"- {prop['name']}: ${prop['price']}\n"
        
        if game_state.dice_roll:
            prompt += f"\nDice Roll: {game_state.dice_roll[0]} + {game_state.dice_roll[1]} = {sum(game_state.dice_roll)}\n"
        
        if game_state.special_situation:
            prompt += f"\nSpecial Situation: {game_state.special_situation}\n"
        
        return prompt
    
    def decide_purchase(self, property_info: Dict[str, Any], game_state: GameState) -> bool:
        """
        Use ChatGPT to decide whether to purchase a property.
        
        Args:
            property_info: Information about the property to purchase
            game_state: Current game state
            
        Returns:
            bool: True if AI decides to purchase, False otherwise
        """
        system_prompt = """You are an expert Monopoly player. Analyze the game state and decide whether to purchase the offered property. 
        Consider: property value, rent potential, color group completion, cash flow, and strategic position.
        Respond with either 'YES' or 'NO' followed by a brief explanation."""
        
        game_prompt = self._format_game_state(game_state)
        property_prompt = f"""
PROPERTY OFFER:
Name: {property_info['name']}
Price: ${property_info['price']}
Rent: ${property_info.get('rent', 0)}
Color Group: {property_info.get('color_group', 'Unknown')}

Should I purchase this property?
"""
        
        full_prompt = game_prompt + property_prompt
        response = self._make_api_request(full_prompt, system_prompt)
        
        # Parse the response
        decision = response.upper().startswith('YES')
        
        # Log the decision
        self.decision_history.append({
            'type': 'purchase',
            'property': property_info['name'],
            'decision': decision,
            'reasoning': response
        })
        
        return decision
    
    def decide_jail_action(self, game_state: GameState) -> str:
        """
        Use ChatGPT to decide jail action: 'pay', 'roll', or 'card'.
        
        Args:
            game_state: Current game state
            
        Returns:
            str: Action to take ('pay', 'roll', or 'card')
        """
        system_prompt = """You are in jail in Monopoly. Decide the best action:
        - 'pay': Pay $50 fine to get out immediately
        - 'roll': Try to roll doubles (free, but might stay in jail)
        - 'card': Use Get Out of Jail Free card (if available)
        
        Respond with only the action word followed by brief reasoning."""
        
        game_prompt = self._format_game_state(game_state)
        jail_prompt = f"""
JAIL SITUATION:
Turns in jail: {self.jail_turns}
Get Out of Jail Free cards: {self.get_out_of_jail_free}
Current cash: ${self.money}

What action should I take?
"""
        
        full_prompt = game_prompt + jail_prompt
        response = self._make_api_request(full_prompt, system_prompt)
        
        # Parse response for action
        response_lower = response.lower()
        if 'pay' in response_lower:
            action = 'pay'
        elif 'card' in response_lower and self.get_out_of_jail_free > 0:
            action = 'card'
        else:
            action = 'roll'
        
        # Log the decision
        self.decision_history.append({
            'type': 'jail_action',
            'action': action,
            'reasoning': response
        })
        
        return action
    
    def decide_trade(self, trade_offer: Dict[str, Any], game_state: GameState) -> bool:
        """
        Use ChatGPT to decide whether to accept a trade offer.
        
        Args:
            trade_offer: Details of the trade offer
            game_state: Current game state
            
        Returns:
            bool: True if AI accepts the trade, False otherwise
        """
        system_prompt = """You are evaluating a trade offer in Monopoly. Consider property values, 
        monopoly potential, cash flow, and strategic advantages. 
        Respond with 'ACCEPT' or 'REJECT' followed by reasoning."""
        
        game_prompt = self._format_game_state(game_state)
        trade_prompt = f"""
TRADE OFFER:
Offering: {trade_offer.get('offering', 'Nothing')}
Requesting: {trade_offer.get('requesting', 'Nothing')}
Cash involved: ${trade_offer.get('cash', 0)}

Should I accept this trade?
"""
        
        full_prompt = game_prompt + trade_prompt
        response = self._make_api_request(full_prompt, system_prompt)
        
        # Parse the response
        decision = response.upper().startswith('ACCEPT')
        
        # Log the decision
        self.decision_history.append({
            'type': 'trade',
            'offer': trade_offer,
            'decision': decision,
            'reasoning': response
        })
        
        return decision
    
    def decide_mortgage_action(self, financial_need: int, game_state: GameState) -> List[str]:
        """
        Use ChatGPT to decide which properties to mortgage when needing cash.
        
        Args:
            financial_need: Amount of money needed
            game_state: Current game state
            
        Returns:
            List[str]: List of property names to mortgage
        """
        system_prompt = """You need to raise money in Monopoly by mortgaging properties. 
        Choose which properties to mortgage to meet your financial needs while maintaining 
        the best strategic position. List property names to mortgage."""
        
        game_prompt = self._format_game_state(game_state)
        mortgage_prompt = f"""
FINANCIAL SITUATION:
Money needed: ${financial_need}
Current cash: ${self.money}

Available properties to mortgage:
"""
        for prop in self.properties:
            mortgage_prompt += f"- {getattr(prop, 'name', 'Unknown')}: Mortgage value ${getattr(prop, 'mortgage_value', 0)}\n"
        
        mortgage_prompt += "\nWhich properties should I mortgage? List them by name."
        
        full_prompt = game_prompt + mortgage_prompt
        response = self._make_api_request(full_prompt, system_prompt)
        
        # Parse property names from response
        property_names = []
        for prop in self.properties:
            prop_name = getattr(prop, 'name', '')
            if prop_name.lower() in response.lower():
                property_names.append(prop_name)
        
        # Log the decision
        self.decision_history.append({
            'type': 'mortgage',
            'need': financial_need,
            'properties': property_names,
            'reasoning': response
        })
        
        return property_names
    
    def get_decision_history(self) -> List[Dict[str, Any]]:
        """Return the AI's decision history for analysis."""
        return self.decision_history.copy()
    
    def clear_decision_history(self) -> None:
        """Clear the decision history."""
        self.decision_history.clear()
    
    def __str__(self) -> str:
        base_str = super().__str__()
        return base_str.replace("Player(", "AIPlayer(")


if __name__ == "__main__":
    # Basic test
    try:
        ai_player = AIPlayer(name="AI Bot", token="🤖", api_key="test-key")
        print("AI Player created:", ai_player)
        
        # Test game state creation
        game_state = GameState(
            current_player="AI Bot",
            board_position=5,
            money=1200,
            properties=["Mediterranean Avenue"],
            other_players=[{"name": "Human", "money": 1500, "properties": []}],
            available_properties=[{"name": "Baltic Avenue", "price": 60}]
        )
        
        print("Game state created for testing")
        
    except ValueError as e:
        print(f"Error: {e}")
        print("Set OPENAI_API_KEY environment variable to test")
