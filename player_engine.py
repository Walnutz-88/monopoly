import argparse
import asyncio
import json
import httpx
import redis.asyncio as aioredis
import websockets
import os
import sys

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


async def post_purchase_decision(player, position, decision):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/purchase", json={"player": player, "position": position, "decision": decision}
        )
        return response


async def get_user_purchase_decision(message):
    """Get user's purchase decision (y/n)"""
    def input_thread():
        while True:
            decision = input(f"{message} (y/n): ").strip().lower()
            if decision in ['y', 'n']:
                return decision
            print("Please enter 'y' for yes or 'n' for no.")
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input_thread)


async def wait_for_user_input(message="\nPress Enter to continue..."):
    """Wait for user to press Enter to continue"""
    def input_thread():
        input(message)
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, input_thread)


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

    print(json.dumps(board, indent=2))

    if board["state"] != "is_playing":
        print("Game over.")
        return False  # Return False to indicate no move was made

    current_turn_player = str(board["player_turn"] + 1)
    if current_turn_player == i_am_playing:
        # Wait for user to press Enter to start their turn (first prompt)
        if wait_for_start and not args.auto:
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
                    if not args.auto:
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
    print("Manual mode: Press Enter to start your turn, then press Enter again to end your turn.")
    print("Other player moves are automatic.")
    
    # Handle initial board state
    board = await get_board()
    if board and board["state"] == "is_playing":
        current_turn_player = str(board["player_turn"] + 1)
        i_made_move = await handle_board_state(websocket, wait_for_start=(current_turn_player == i_am_playing), publish_update=False)
        # Second prompt: wait for Enter to end turn after making a move
        if i_made_move and not args.auto:
            await wait_for_user_input("\nPress Enter to end your turn: ")
            # Now publish the update to notify the other player
            await r.publish(redisPubSubKey, "update")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                print("\nReceived update!")
                board = await get_board()
                if board and board["state"] == "is_playing":
                    current_turn_player = str(board["player_turn"] + 1)
                    i_made_move = await handle_board_state(websocket, wait_for_start=(current_turn_player == i_am_playing), publish_update=False)
                    # Second prompt: wait for Enter to end turn after making a move
                    if i_made_move and not args.auto:
                        await wait_for_user_input("\nPress Enter to end your turn: ")
                        # Now publish the update to notify the other player
                        await r.publish(redisPubSubKey, "update")
                else:
                    # Game over or other state, just handle normally
                    await handle_board_state(websocket)
    except asyncio.CancelledError:
        print("\nConnection cancelled.")
    except Exception as e:
        print(f"\nError in listen_for_updates: {e}")
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
        print(f"\nError in listen_for_updates: {e}")
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