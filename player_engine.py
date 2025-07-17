import argparse
import asyncio
import json
import httpx
import redis.asyncio as aioredis
import websockets
import os
import sys
import requests
from typing import Dict, Any, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, environment variables will be loaded from system
    pass

redisPubSubKey = "monopoly_game_state_changed"

# CLI argument parsing - only when run directly
parser = argparse.ArgumentParser(description="Monopoly Game Client")
parser.add_argument(
    "--player", choices=["1", "2", "3", "4", "5", "6"], help="Which player are you?"
)
parser.add_argument(
    "--reset", action="store_true", help="Reset the board before starting the game."
)
parser.add_argument(
    "--auto", action="store_true", help="Automatic mode - runs continuously without waiting for input."
)
parser.add_argument(
    "--ai", action="store_true", help="Enable AI mode - uses ChatGPT to make decisions."
)

# Initialize defaults for when imported as module
args = None
i_am_playing = None
WS_URL = f"ws://ai.thewcl.com:8703"

# Redis Pub/Sub setup
r = aioredis.Redis(
    host="ai.thewcl.com", port=6379, db=3, password="atmega328", decode_responses=True
)
redisPubSubKey = "monopoly_game_state_changed"

# FastAPI base URL
BASE_URL = "http://localhost:8000"

# AI Configuration
AI_SERVER_URL = "http://ai.thewcl.com:6502"
AI_MODEL = "gpt-4.1-nano"


async def get_num_players():
    """Get number of players from user input"""
    def input_thread():
        while True:
            try:
                num_players = int(input("How many players? (2-6): "))
                if 2 <= num_players <= 6:
                    return num_players
                else:
                    print("Please enter a number between 2 and 6.")
            except ValueError:
                print("Please enter a valid number.")
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input_thread)

async def reset_board():
    # Prompt for number of players
    num_players = await get_num_players()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/reset", json={"num_players": num_players})
        print(f"Reset response status: {response.status_code}")
        print(f"Reset response headers: {response.headers}")
        print(f"Reset response content: {response.text}")
        
        if response.status_code == 200:
            try:
                if response.text.strip():  # Check if response has content
                    result = response.json()
                    print("Game reset:", result)
                    print(f"\nYou can now run the following commands in separate terminal windows:")
                    for i in range(1, num_players + 1):
                        print(f"  uv run player_engine.py --player {i}")
                else:
                    print("Game reset: Empty response (success)")
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response: {e}")
                print(f"Raw response: {response.text}")
        else:
            print(f"Reset failed with status {response.status_code}: {response.text}")


async def get_board():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/state")
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response from /state: {e}")
                print(f"Raw response: {response.text}")
                return None
        else:
            print(f"Failed to get board state: {response.status_code} - {response.text}")
            return None


async def post_move(player):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/move", json={"player": player, "index": 0}
        )
        return response


async def make_ai_request(prompt: str, system_prompt: str = None) -> str:
    """
    Make a request to the ChatGPT API through the ai.thewcl.com server.
    
    Args:
        prompt: The user prompt for ChatGPT
        system_prompt: Optional system prompt to set context
        
    Returns:
        str: The AI's response
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Warning: No OpenAI API key found. Using fallback decision.")
        return "I'll make a conservative choice."
    
    try:
        payload = {
            "model": AI_MODEL,
            "system_prompt": system_prompt or "You are an AI playing Monopoly. Make strategic decisions based on the game state.",
            "user_prompt": prompt
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        def sync_request():
            response = requests.post(
                f"{AI_SERVER_URL}/chat",
                json=payload,
                headers=headers,
                timeout=30
            )
            return response
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, sync_request)
        
        if response.status_code == 200:
            result = response.json()
            # Parse the actual API response format
            if isinstance(result, dict):
                # Try to extract from the actual API format
                if "output" in result and len(result["output"]) > 0:
                    output = result["output"][0]
                    if "content" in output and len(output["content"]) > 0:
                        content = output["content"][0]
                        if "text" in content:
                            return content["text"].strip()
                # Fallback to other possible formats
                if "content" in result:
                    return result["content"].strip()
                elif "response" in result:
                    return result["response"].strip()
                else:
                    # If it's just a string response
                    return str(result).strip()
            else:
                # If it's a string response
                return str(result).strip()
        else:
            print(f"AI API Error: {response.status_code} - {response.text}")
            return "I need to think about this more carefully."
            
    except Exception as e:
        print(f"Error making AI request: {e}")
        return "I'll make a conservative choice."


async def ai_decide_purchase(player: str, property_info: Dict[str, Any]) -> bool:
    """
    Use AI to decide whether to purchase a property.

    Args:
        player: Player's name
        property_info: Information about the property

    Returns:
        bool: Decision to purchase (True/False)
    """
    prompt = f"Player {player}, should you buy {property_info['name']} for ${property_info['buy_price']}? Respond with 'yes' or 'no'."
    response = await make_ai_request(prompt)
    return 'yes' in response.lower()


async def post_purchase_decision(player, position, decision):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/purchase", json={"player": player, "position": position, "decision": decision}
        )
        return response


async def ai_decide_house_purchase(player, options):
    """Use AI to decide which house to buy from available options.
    
    Args:
        player: The player name
        options: List of house buying options
    
    Returns:
        The selected option dict, or None if AI decides not to buy
    """
    if not options:
        return None
    
    # Get current board state for better AI decision making
    board = await get_board()
    player_index = int(player.split()[-1]) - 1  # Extract player number
    player_money = 0
    
    if board and board.get("players") and 0 <= player_index < len(board["players"]):
        player_money = board["players"][player_index]["money"]
    
    # Format options for AI prompt
    options_text = "\n".join([f"{i+1}. {option['description']} (Cost: ${option['house_cost']})" 
                              for i, option in enumerate(options)])
    
    prompt = f"""You are Player {player} in a Monopoly game. You have ${player_money} in cash.

You have the following house buying options:
{options_text}

Consider your current financial situation and strategic position. Which house should you buy, if any?

Respond with either:
- The number of the option you want to buy (1, 2, 3, etc.)
- "none" if you don't want to buy any houses

Your response:"""
    
    response = await make_ai_request(prompt)
    
    # Parse AI response
    response_lower = response.lower().strip()
    
    if "none" in response_lower:
        return None
    
    # Try to extract option number
    for i, option in enumerate(options, 1):
        if str(i) in response_lower:
            return option
    
    # If no clear choice, default to None (don't buy)
    return None


async def get_house_options(player):
    """Get house buying options for a player."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/house_options/{player}")
        if response.status_code == 200:
            return response.json().get("options", [])
        else:
            print(f"Failed to get house options: {response.status_code} - {response.text}")
            return []


async def buy_house(player, position):
    """Buy a house for a player at a specific position."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/buy_house", json={"player": player, "position": position}
        )
        return response


async def get_user_house_decision(options):
    """Get user's house buying decision."""
    def input_thread():
        while True:
            try:
                print("\n🏠 House Buying Options:")
                if not options:
                    print("No house buying options available.")
                    return None
                
                for i, option in enumerate(options, 1):
                    print(f"  {i}. {option['description']}")
                
                print("  0. Skip buying houses")
                
                choice = input("Choose an option (0 to skip): ").strip()
                
                if choice == '0':
                    return None
                
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(options):
                        return options[choice_num - 1]
                    else:
                        print(f"Please enter a number between 0 and {len(options)}.")
                except ValueError:
                    print("Please enter a valid number.")
                    
            except EOFError:
                print("\nEOF detected, skipping house buying")
                return None
            except KeyboardInterrupt:
                print("\nKeyboard interrupt detected, skipping house buying")
                return None
            except Exception as e:
                print(f"\nError in input: {e}, skipping house buying")
                return None
    
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(loop.run_in_executor(None, input_thread), timeout=300)  # 5 minute timeout
    except asyncio.TimeoutError:
        print("\nTimeout waiting for house buying decision, skipping")
        return None


async def handle_house_buying(player_name):
    """Handle the house buying process for a player."""
    options = await get_house_options(player_name)
    
    if not options:
        return  # No options available
    
    if args.ai:
        # AI mode - use AI to decide which house to buy
        print(f"🤖 AI considering house purchases for {player_name}...")
        selected_option = await ai_decide_house_purchase(player_name, options)
        
        if selected_option:
            print(f"🤖 AI buying house: {selected_option['description']}")
            
            response = await buy_house(player_name, selected_option['position'])
            if response.status_code == 200:
                result = response.json()
                print(f"🤖 {result.get('message', '')}")
            else:
                print(f"🤖 Failed to buy house: {response.status_code} - {response.text}")
        else:
            print(f"🤖 AI decided not to buy any houses")
    elif not args.auto:
        # Manual mode - ask user
        selected_option = await get_user_house_decision(options)
        
        if selected_option:
            print(f"Buying house: {selected_option['description']}")
            
            response = await buy_house(player_name, selected_option['position'])
            if response.status_code == 200:
                result = response.json()
                print(result.get('message', ''))
            else:
                print(f"Failed to buy house: {response.status_code} - {response.text}")
    else:
        # Auto mode - simple logic: buy cheapest house if enough money
        board = await get_board()
        if board and board.get("players"):
            player_index = int(player_name.split()[-1]) - 1  # Extract player number
            if 0 <= player_index < len(board["players"]):
                player_money = board["players"][player_index]["money"]
                
                # Find cheapest house option
                cheapest_option = min(options, key=lambda x: x['house_cost'])
                if player_money >= cheapest_option['house_cost']:
                    print(f"Auto buying house: {cheapest_option['description']}")
                    
                    response = await buy_house(player_name, cheapest_option['position'])
                    if response.status_code == 200:
                        result = response.json()
                        print(result.get('message', ''))
                    else:
                        print(f"Failed to buy house: {response.status_code} - {response.text}")


async def get_user_purchase_decision(message):
    """Get user's purchase decision (y/n)"""
    def input_thread():
        while True:
            try:
                decision = input(f"{message} (y/n): ").strip().lower()
                if decision in ['y', 'n']:
                    return decision
                print("Please enter 'y' for yes or 'n' for no.")
            except EOFError:
                print("\nEOF detected, defaulting to 'n'")
                return 'n'
            except KeyboardInterrupt:
                print("\nKeyboard interrupt detected, defaulting to 'n'")
                return 'n'
            except Exception as e:
                print(f"\nError in input: {e}, defaulting to 'n'")
                return 'n'
    
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(loop.run_in_executor(None, input_thread), timeout=300)  # 5 minute timeout
    except asyncio.TimeoutError:
        print("\nTimeout waiting for purchase decision, defaulting to 'n'")
        return 'n'


async def wait_for_user_input(message="\nPress Enter to continue..."):
    """Wait for user to press Enter to continue"""
    def input_thread():
        try:
            input(message)
        except EOFError:
            print("\nEOF detected, continuing...")
        except KeyboardInterrupt:
            print("\nKeyboard interrupt detected, continuing...")
        except Exception as e:
            print(f"\nError in input: {e}")
    
    loop = asyncio.get_event_loop()
    try:
        await asyncio.wait_for(loop.run_in_executor(None, input_thread), timeout=300)  # 5 minute timeout
    except asyncio.TimeoutError:
        print("\nTimeout waiting for input, continuing...")


async def display_current_player_money():
    """Display the current player's money and owned properties"""
    board = await get_board()
    if board and board.get("players"):
        player_index = int(i_am_playing) - 1  # Convert to 0-based index
        if 0 <= player_index < len(board["players"]):
            player_money = board["players"][player_index]["money"]
            print(f"\n💰 You currently have ${player_money}")
            
            # Display owned properties
            owned_properties = []
            
            # Check regular properties
            for prop in board.get("regular_properties", []):
                if prop.get("owner") == f"Player {i_am_playing}":
                    houses = prop.get("house_count", 0)
                    house_info = f" ({houses} houses)" if houses > 0 else ""
                    owned_properties.append(f"  📋 {prop['name']} ({prop['color']}){house_info}")
            
            # Check railroad properties
            for prop in board.get("railroad_properties", []):
                if prop.get("owner") == f"Player {i_am_playing}":
                    owned_properties.append(f"  🚂 {prop['name']}")
            
            # Check utility properties
            for prop in board.get("utility_properties", []):
                if prop.get("owner") == f"Player {i_am_playing}":
                    owned_properties.append(f"  ⚡ {prop['name']}")
            
            if owned_properties:
                print("\n🏠 Your properties:")
                for prop in owned_properties:
                    print(prop)
            else:
                print("\n🏠 You don't own any properties yet")


async def send_positions_over_websocket(websocket):
    board = await get_board()
    if board is None:
        print("Cannot send positions - failed to get board state")
        return
    
    positions = board.get("positions")
    if isinstance(positions, list) and len(positions) == 9:
        await websocket.send(json.dumps({"positions": positions}))


async def handle_board_state(websocket, wait_for_start=False, publish_update=True):
    board = await get_board()
    
    if board is None:
        print("Failed to get board state")
        return False  # Return False to indicate no move was made

    if board["state"] != "is_playing":
        print("Game over.")
        return False  # Return False to indicate no move was made

    current_turn_player = str(board["player_turn"] + 1)
    if current_turn_player == i_am_playing:
        # Check for house buying opportunities at the start of turn
        player_name = f"Player {i_am_playing}"
        await handle_house_buying(player_name)
        
        # Wait for user to press Enter to start their turn (first prompt)
        if wait_for_start and not args.auto and not args.ai:
            await wait_for_user_input("\nIt's your turn, press Enter to roll: ")
        
        print("Rolling Dice...")
        player_name = f"Player {i_am_playing}"
        response = await post_move(player_name)
        if response.status_code == 200:
            try:
                result = response.json()
                print(result.get("message", ""))
                space_details = result.get("space_details")
                if space_details:
                    print("Space Details:", space_details)
                
                # Check if this is a property that can be bought
                if (space_details and 
                    space_details.get("type") in ["regular_property", "railroad_property", "utility_property"] and
                    space_details.get("owner") is None and
                    result.get("message", "").startswith(f"{player_name} rolled") and
                    "Can buy" in result.get("message", "")):
                    
                    property_name = space_details.get("name")
                    buy_price = space_details.get("buy_price")
                    current_position = space_details.get("position")
                    
                    # Ask for purchase decision
                    if args.ai:
                        # AI mode - use ChatGPT to make decision
                        print(f"🤖 AI is deciding whether to buy {property_name} for ${buy_price}...")
                        ai_decision = await ai_decide_purchase(player_name, space_details)
                        decision = "y" if ai_decision else "n"
                        print(f"🤖 AI decision: {decision} for {property_name} at ${buy_price}")
                    elif not args.auto:
                        decision = await get_user_purchase_decision(f"Do you want to buy {property_name} for ${buy_price}?")
                    else:
                        # Auto mode - make a simple decision based on price
                        decision = "y" if buy_price <= 200 else "n"
                        print(f"Auto decision: {decision} for {property_name} at ${buy_price}")
                    
                    # Send the purchase decision
                    purchase_response = await post_purchase_decision(player_name, current_position, decision)
                    
                    if purchase_response.status_code == 200:
                        try:
                            purchase_result = purchase_response.json()
                            print(purchase_result.get("message", ""))
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse JSON response from /purchase: {e}")
                            print(f"Raw response: {purchase_response.text}")
                    else:
                        print(f"Purchase decision failed with status {purchase_response.status_code}: {purchase_response.text}")
                
                # Only publish update if explicitly requested (for auto mode or after manual turn end)
                if publish_update:
                    await r.publish(redisPubSubKey, "update")
                await send_positions_over_websocket(websocket)
                return True  # Return True to indicate we made a move
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response from /move: {e}")
                print(f"Raw response: {response.text}")
        else:
            print(f"Move failed with status {response.status_code}: {response.text}")
    else:
        print(f"It's Player {current_turn_player}'s turn")

    await send_positions_over_websocket(websocket)
    return False  # Return False to indicate we didn't make a move


async def listen_for_updates_manual(websocket):
    """Manual step-through mode - two prompts per turn: start turn and end turn"""
    pubsub = r.pubsub()
    await pubsub.subscribe(redisPubSubKey)
    print(f"Subscribed to {redisPubSubKey}. Waiting for updates...\n")
    if args.ai:
        print("AI mode: Fully automated - AI will make all decisions and moves automatically.")
    else:
        print("Manual mode: Press Enter to start your turn, then press Enter again to end your turn.")
    print("Other player moves are automatic.")
    
    # Handle initial board state
    board = await get_board()
    if board and board["state"] == "is_playing":
        current_turn_player = str(board["player_turn"] + 1)
        i_made_move = await handle_board_state(websocket, wait_for_start=(current_turn_player == i_am_playing), publish_update=False)
        # Second prompt: wait for Enter to end turn after making a move
        if i_made_move and not args.auto and not args.ai:
            await display_current_player_money()
            await wait_for_user_input("\nPress Enter to end your turn: ")
            # Now publish the update to notify the other player
            await r.publish(redisPubSubKey, "update")
        elif i_made_move and args.ai:
            # AI mode: show money but auto-continue
            await display_current_player_money()
            print("🤖 AI ending turn automatically...")
            # Now publish the update to notify the other player
            await r.publish(redisPubSubKey, "update")
        elif i_made_move and args.auto:
            # Auto mode: show money
            await display_current_player_money()

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                print("\nReceived update!")
                board = await get_board()
                if board and board["state"] == "is_playing":
                    current_turn_player = str(board["player_turn"] + 1)
                    i_made_move = await handle_board_state(websocket, wait_for_start=(current_turn_player == i_am_playing), publish_update=False)
                    # Second prompt: wait for Enter to end turn after making a move
                    if i_made_move and not args.auto and not args.ai:
                        await display_current_player_money()
                        
                        # Offer house buying options
                        await handle_house_buying(f"Player {i_am_playing}")
                        
                        await wait_for_user_input("\nPress Enter to end your turn: ")
                        # Now publish the update to notify the other player
                        await r.publish(redisPubSubKey, "update")
                    elif i_made_move and args.ai:
                        # AI mode: show money but auto-continue
                        await display_current_player_money()
                        
                        # AI house buying
                        await handle_house_buying(f"Player {i_am_playing}")
                        
                        print("🤖 AI ending turn automatically...")
                        # Now publish the update to notify the other player
                        await r.publish(redisPubSubKey, "update")
                    elif i_made_move and args.auto:
                        # Auto mode: show money and handle house buying
                        await display_current_player_money()
                        
                        # Auto house buying
                        await handle_house_buying(f"Player {i_am_playing}")
                else:
                    # Game over or other state, just handle normally
                    await handle_board_state(websocket)
    except asyncio.CancelledError:
        print("\nConnection cancelled.")
    except Exception as e:
        import traceback
        print(f"\nError in listen_for_updates: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Full traceback:")
        traceback.print_exc()
    finally:
        await pubsub.unsubscribe(redisPubSubKey)
        await pubsub.aclose()


async def listen_for_updates(websocket):
    """Original automatic mode"""
    pubsub = r.pubsub()
    await pubsub.subscribe(redisPubSubKey)
    print(f"Subscribed to {redisPubSubKey}. Waiting for updates...\n")
    await handle_board_state(websocket)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                print("\nReceived update!")
                await handle_board_state(websocket)
    except asyncio.CancelledError:
        print("\nConnection cancelled.")
    except Exception as e:
        import traceback
        print(f"\nError in listen_for_updates: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Full traceback:")
        traceback.print_exc()
    finally:
        await pubsub.unsubscribe(redisPubSubKey)
        await pubsub.aclose()


async def main():
    if args.reset:
        await reset_board()
        return

    try:
        async with websockets.connect(WS_URL) as websocket:
            if args.auto:
                await listen_for_updates(websocket)
            else:
                await listen_for_updates_manual(websocket)
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    args = parser.parse_args()
    
    # Validate arguments
    if not args.reset and not args.player:
        parser.error("--player is required when not using --reset")
    
    i_am_playing = args.player
    
    if not args.reset:
        print(f"Connecting to WebSocket server at {WS_URL}")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")