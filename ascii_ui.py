import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import asyncio
import websockets
import json
import os
import argparse
import threading
import requests
import random
import time

# WebSocket URL
WS_URL = "ws://ai.thewcl.com:8703"
API_URL = "http://localhost:8000"

class MonopolyUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Monopoly Game")
        self.root.geometry("1400x800")
        self.websocket = None
        self.game_started = False
        self.current_player = None
        self.player_count = 2
        self.dice_values = (1, 1)
        self.board_positions = []
        self.game_state = {}
        
        # Initialize board positions (40 spaces in Monopoly)
        self.init_board_positions()
        
        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Setup UI
        self.setup_waiting_screen()
        
        # Start WebSocket connection in background
        self.start_websocket_connection()
        
        # Start polling for game state changes
        self.start_game_state_polling()
    
    def init_board_positions(self):
        """Initialize the monopoly board positions"""
        self.board_spaces = [
            "GO", "Mediterranean Ave", "Community Chest", "Baltic Ave", "Income Tax",
            "Reading Railroad", "Oriental Ave", "Chance", "Vermont Ave", "Connecticut Ave",
            "Jail", "St. Charles Place", "Electric Company", "States Ave", "Virginia Ave",
            "Pennsylvania Railroad", "St. James Place", "Community Chest", "Tennessee Ave", "New York Ave",
            "Free Parking", "Kentucky Ave", "Chance", "Indiana Ave", "Illinois Ave",
            "B. & O. Railroad", "Atlantic Ave", "Ventnor Ave", "Water Works", "Marvin Gardens",
            "Go to Jail", "Pacific Ave", "N. Carolina Ave", "Community Chest", "Pennsylvania Ave",
            "Short Line", "Chance", "Park Place", "Luxury Tax", "Boardwalk"
        ]
        
        # Color coding for properties
        self.space_colors = {
            "Mediterranean Ave": "#5A2F1D", "Baltic Ave": "#5A2F1D",
            "Oriental Ave": "#4682B4", "Vermont Ave": "#4682B4", "Connecticut Ave": "#4682B4",
            "St. Charles Place": "#C71585", "States Ave": "#C71585", "Virginia Ave": "#C71585",
            "St. James Place": "#CD853F", "Tennessee Ave": "#CD853F", "New York Ave": "#CD853F",
            "Kentucky Ave": "#B22222", "Indiana Ave": "#B22222", "Illinois Ave": "#B22222",
            "Atlantic Ave": "#BDB76B", "Ventnor Ave": "#BDB76B", "Marvin Gardens": "#BDB76B",
            "Pacific Ave": "#228B22", "N. Carolina Ave": "#228B22", "Pennsylvania Ave": "#228B22",
            "Park Place": "#4169E1", "Boardwalk": "#4169E1"
        }
    
    def setup_waiting_screen(self):
        """Setup the waiting screen that shows instructions for terminal setup"""
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Title Label
        self.title_label = ttk.Label(self.main_frame, text="Welcome to Monopoly", font=("Helvetica", 20))
        self.title_label.pack(pady=20)

        # Instructions
        instructions = (
            "To start the game, please use the terminal:\n\n"
            "1. Reset the game with desired number of players:\n"
            "   uv run player_engine.py --reset\n\n"
            "2. Start player terminals (in separate windows):\n"
            "   uv run player_engine.py --player 1\n"
            "   uv run player_engine.py --player 2\n"
            "   (and so on for each player)\n\n"
            "The game board will appear here once the game starts."
        )
        
        self.instructions_label = ttk.Label(self.main_frame, text=instructions, font=("Helvetica", 12), justify=tk.LEFT)
        self.instructions_label.pack(pady=20)
        
        # Status label
        self.status_label = ttk.Label(self.main_frame, text="Waiting for game to start...", font=("Helvetica", 12, "italic"))
        self.status_label.pack(pady=10)
        
        # Add a progress indicator
        self.progress_label = ttk.Label(self.main_frame, text="Checking for game state...", font=("Helvetica", 10))
        self.progress_label.pack(pady=5)
    
    def setup_game_screen(self):
        """Setup the main game screen with monopoly board and controls"""
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Create main layout with board on left and controls on right
        self.game_container = ttk.Frame(self.main_frame)
        self.game_container.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Monopoly Board
        self.board_frame = ttk.LabelFrame(self.game_container, text="Monopoly Board", padding="10")
        self.board_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Right side - Game Status
        self.status_frame = ttk.LabelFrame(self.game_container, text="Game Status", padding="10")
        self.status_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.status_frame.config(width=350)
        
        # Setup board
        self.setup_board()
        
        # Setup status panel
        self.setup_status_panel()
        
        # Request initial game state
        self.request_game_state()
    
    def setup_board(self):
        """Setup the monopoly board display"""
        # Create canvas for the board
        self.board_canvas = tk.Canvas(self.board_frame, width=600, height=600, bg="white")
        self.board_canvas.pack()
        
        # Draw the board
        self.draw_board()
    
    def draw_board(self):
        """Draw the monopoly board"""
        self.board_canvas.delete("all")
        
        # Board dimensions - 11x11 grid
        cell_size = 50
        board_size = 11 * cell_size  # 550 pixels for 11x11 grid
        start_x = 25
        start_y = 25
        
        # Draw board outline
        self.board_canvas.create_rectangle(start_x, start_y, start_x + board_size, start_y + board_size, 
                                         outline="black", width=2)
        
        # Draw spaces around the board
        self.board_spaces_rects = []
        
        # Bottom row (0-10) - 11 squares with GO at bottom-right corner
        for i in range(11):
            x = start_x + board_size - ((i+1) * cell_size)
            y = start_y + board_size - cell_size
            space_idx = i
            space_name = self.board_spaces[space_idx] if space_idx < len(self.board_spaces) else f"Space {space_idx}"
            color = self.space_colors.get(space_name, "white")
            
            rect = self.board_canvas.create_rectangle(x, y, x + cell_size, y + cell_size, 
                                                    fill=color, outline="black", width=1)
            self.board_spaces_rects.append(rect)
            
            # Add text with full name
            self.board_canvas.create_text(x + cell_size//2, y + cell_size//2, 
                                        text=space_name, font=("Arial", 7), fill="black", width=cell_size-4)
        
        # Left side (11-20) - 9 squares (excluding corners)
        for i in range(9):
            x = start_x
            y = start_y + board_size - cell_size - ((i+1) * cell_size)
            space_idx = i + 11
            space_name = self.board_spaces[space_idx] if space_idx < len(self.board_spaces) else f"Space {space_idx}"
            color = self.space_colors.get(space_name, "white")
            
            rect = self.board_canvas.create_rectangle(x, y, x + cell_size, y + cell_size, 
                                                    fill=color, outline="black", width=1)
            self.board_spaces_rects.append(rect)
            
            # Add text with full name
            self.board_canvas.create_text(x + cell_size//2, y + cell_size//2, 
                                        text=space_name, font=("Arial", 7), fill="black", width=cell_size-4)
        
        # Top row (20-30) - 11 squares
        for i in range(11):
            x = start_x + (i * cell_size)
            y = start_y
            space_idx = i + 20
            space_name = self.board_spaces[space_idx] if space_idx < len(self.board_spaces) else f"Space {space_idx}"
            color = self.space_colors.get(space_name, "white")
            
            rect = self.board_canvas.create_rectangle(x, y, x + cell_size, y + cell_size, 
                                                    fill=color, outline="black", width=1)
            self.board_spaces_rects.append(rect)
            
            # Add text with full name
            self.board_canvas.create_text(x + cell_size//2, y + cell_size//2, 
                                        text=space_name, font=("Arial", 7), fill="black", width=cell_size-4)
        
        # Right side (31-39) - 9 squares (excluding corners)
        for i in range(9):
            x = start_x + board_size - cell_size
            y = start_y + ((i+1) * cell_size)
            space_idx = i + 31
            space_name = self.board_spaces[space_idx] if space_idx < len(self.board_spaces) else f"Space {space_idx}"
            color = self.space_colors.get(space_name, "white")
            
            rect = self.board_canvas.create_rectangle(x, y, x + cell_size, y + cell_size, 
                                                    fill=color, outline="black", width=1)
            self.board_spaces_rects.append(rect)
            
            # Add text with full name
            self.board_canvas.create_text(x + cell_size//2, y + cell_size//2, 
                                        text=space_name, font=("Arial", 7), fill="black", width=cell_size-4)
        
        # Draw center area
        center_x = start_x + cell_size + 20
        center_y = start_y + cell_size + 20
        center_width = board_size - 2 * cell_size - 40
        center_height = board_size - 2 * cell_size - 40
        
        self.board_canvas.create_rectangle(center_x, center_y, center_x + center_width, center_y + center_height,
                                         fill="lightgray", outline="black", width=1)
        
        self.board_canvas.create_text(center_x + center_width//2, center_y + center_height//2,
                                    text="MONOPOLY", font=("Arial", 24, "bold"))
        
        # Draw player positions
        self.draw_player_positions()
    
    def draw_player_positions(self):
        """Draw player tokens on the board"""
        if not self.game_state.get('players'):
            return
        
        # Clear existing player tokens
        self.board_canvas.delete("player_token")
        
        # Player colors
        player_colors = ["red", "blue", "green", "yellow", "purple", "orange"]
        
        # Use same dimensions as board
        cell_size = 50
        board_size = 11 * cell_size
        start_x = 25
        start_y = 25
        
        for i, player in enumerate(self.game_state['players']):
            position = player.get('position', 0)
            color = player_colors[i % len(player_colors)]
            
            # Calculate position coordinates
            x, y = self.get_position_coordinates(position, start_x, start_y, cell_size, board_size)
            
            # Draw player token
            token_size = 8
            # Position players vertically instead of horizontally
            offset_x = 5
            offset_y = (i % 6) * 8 + 5  # Vertical offset for multiple players on same space
            
            self.board_canvas.create_oval(x + offset_x, y + offset_y, 
                                        x + offset_x + token_size, y + offset_y + token_size,
                                        fill=color, outline="black", width=1, tags="player_token")
            
            # Add player number
            self.board_canvas.create_text(x + offset_x + token_size//2, y + offset_y + token_size//2,
                                        text=str(i+1), font=("Arial", 6, "bold"), 
                                        fill="white", tags="player_token")
    
    def get_position_coordinates(self, position, start_x, start_y, cell_size, board_size):
        """Get x, y coordinates for a board position"""
        if position <= 10:  # Bottom row (0-10) - GO at bottom-right
            x = start_x + board_size - ((position + 1) * cell_size)
            y = start_y + board_size - cell_size
        elif position <= 19:  # Left side (11-19)
            x = start_x
            y = start_y + board_size - ((position - 10 + 1) * cell_size)
        elif position <= 30:  # Top row (20-30)
            x = start_x + ((position - 20) * cell_size)
            y = start_y
        else:  # Right side (31-39)
            x = start_x + board_size - cell_size
            y = start_y + ((position - 30) * cell_size)
        
        return x, y
    
    def setup_status_panel(self):
        """Setup the game status panel"""
        # Current player section
        self.current_player_frame = ttk.LabelFrame(self.status_frame, text="Current Player", padding="10")
        self.current_player_frame.pack(fill=tk.X, pady=5)
        
        self.current_player_label = ttk.Label(self.current_player_frame, text="Player: -", font=("Helvetica", 12, "bold"))
        self.current_player_label.pack(anchor=tk.W)
        
        self.current_money_label = ttk.Label(self.current_player_frame, text="Money: $0")
        self.current_money_label.pack(anchor=tk.W)
        
        self.current_position_label = ttk.Label(self.current_player_frame, text="Position: GO")
        self.current_position_label.pack(anchor=tk.W)
        
        # Add turn indicator
        self.turn_indicator_label = ttk.Label(self.current_player_frame, text="Status: Waiting...", font=("Helvetica", 10, "italic"))
        self.turn_indicator_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Game status section
        self.game_status_frame = ttk.LabelFrame(self.status_frame, text="Game Status", padding="10")
        self.game_status_frame.pack(fill=tk.X, pady=5)
        
        self.game_status_label = ttk.Label(self.game_status_frame, text="Status: Waiting")
        self.game_status_label.pack(anchor=tk.W)
        
        # Player status section
        self.players_frame = ttk.LabelFrame(self.status_frame, text="All Players", padding="10")
        self.players_frame.pack(fill=tk.X, pady=5)
        
        # Game log
        self.log_frame = ttk.LabelFrame(self.status_frame, text="Game Log", padding="5")
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=10, width=35, font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        self.control_frame = ttk.Frame(self.status_frame)
        self.control_frame.pack(fill=tk.X, pady=10)
        
        self.reset_button = ttk.Button(self.control_frame, text="Reset Game", command=self.reset_game)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        self.refresh_button = ttk.Button(self.control_frame, text="Refresh", command=self.request_game_state)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
    

    
    
    
    
    
    
    
    def reset_game(self):
        """Reset the game and return to waiting screen"""
        self.game_started = False
        self.setup_waiting_screen()
    
    def request_game_state(self):
        """Request current game state from WebSocket"""
        if self.websocket:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.websocket.send(json.dumps({"type": "request_game_state"})),
                    self.websocket_loop
                )
            except Exception as e:
                self.log_message(f"Error requesting game state: {str(e)}")
    
    def log_message(self, message):
        """Add message to game log"""
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
    
    def update_game_display(self, game_data):
        """Update the game display with new game data"""
        if not self.game_started:
            return
        
        try:
            # Store the game state
            self.game_state = game_data
            
            # Update current player
            if 'players' in game_data and 'player_turn' in game_data:
                current_player_index = game_data['player_turn']
                if current_player_index < len(game_data['players']):
                    current_player = game_data['players'][current_player_index]
                    self.current_player_label.config(text=f"Player: {current_player['name']}")
                    self.current_money_label.config(text=f"Money: ${current_player['money']}")
                    
                    # Get position name
                    position = current_player['position']
                    position_name = self.board_spaces[position] if position < len(self.board_spaces) else f"Position {position}"
                    self.current_position_label.config(text=f"Position: {position_name}")
                    
                    # Update turn indicator
                    if hasattr(self, 'turn_indicator_label'):
                        self.turn_indicator_label.config(text=f"Status: {current_player['name']}'s turn")
            
            # Update game status
            game_status = game_data.get('state', 'unknown')
            status_text = f"Status: {game_status}"
            if game_status == "is_playing":
                current_turn = game_data.get('player_turn', 0)
                if current_turn < len(game_data.get('players', [])):
                    current_player_name = game_data['players'][current_turn]['name']
                    status_text += f" - {current_player_name}'s turn"
            
            self.game_status_label.config(text=status_text)
            
            # Update players info
            for widget in self.players_frame.winfo_children():
                widget.destroy()
            
            if 'players' in game_data:
                for i, player in enumerate(game_data['players']):
                    position_name = self.board_spaces[player['position']] if player['position'] < len(self.board_spaces) else f"Pos {player['position']}"
                    player_info = f"{player['name']}: ${player['money']}"
                    player_info += f"\n   @ {position_name}"
                    
                    if i == game_data.get('player_turn', -1):
                        player_info += " ← CURRENT TURN"
                        # Use different style for current player
                        player_label = ttk.Label(self.players_frame, text=player_info, font=("Helvetica", 9, "bold"))
                    else:
                        player_label = ttk.Label(self.players_frame, text=player_info, font=("Helvetica", 9))
                    
                    player_label.pack(anchor=tk.W, pady=2)
            
            # Redraw the board with updated positions
            self.draw_player_positions()
            
            # Log the update
            self.log_message(f"Game updated - {status_text}")
        
        except Exception as e:
            self.log_message(f"Error updating display: {str(e)}")
    
    def start_websocket_connection(self):
        """Start WebSocket connection in a separate thread"""
        def run_websocket():
            self.websocket_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.websocket_loop)
            self.websocket_loop.run_until_complete(self.websocket_listener())
        
        websocket_thread = threading.Thread(target=run_websocket, daemon=True)
        websocket_thread.start()
    
    def start_game_state_polling(self):
        """Start polling for game state changes"""
        def poll_game_state():
            while True:
                try:
                    # Get game state from API
                    response = requests.get(f"{API_URL}/state", timeout=5)
                    if response.status_code == 200:
                        game_data = response.json()
                        
                        # Check if game board should be shown (game has been properly reset)
                        # Game is ready when it has players AND properties (properties are only created during reset)
                        if (game_data.get('players') and 
                            len(game_data['players']) >= 2 and
                            game_data.get('regular_properties') and 
                            len(game_data['regular_properties']) > 0):
                            
                            if not self.game_started:
                                # Game properly configured, switch to game screen
                                self.game_started = True
                                self.root.after(0, self.setup_game_screen)
                                self.root.after(0, lambda: self.log_message("Game board loaded! Game configured with players."))
                            
                            # Update game display
                            self.root.after(0, lambda: self.update_game_display(game_data))
                        else:
                            # Game hasn't been properly configured yet, update waiting screen status
                            num_players = len(game_data.get('players', []))
                            has_properties = bool(game_data.get('regular_properties'))
                            
                            if num_players > 0 and has_properties:
                                status_text = f"Game configured with {num_players} players. Ready to play!"
                                # Show player names if available
                                if game_data.get('players'):
                                    player_names = [p['name'] for p in game_data['players']]
                                    status_text += f"\nPlayers: {', '.join(player_names)}"
                            elif num_players > 0:
                                status_text = f"Found {num_players} players, but game needs to be reset first."
                            else:
                                status_text = "Waiting for game to start..."
                            
                            if hasattr(self, 'status_label'):
                                self.root.after(0, lambda: self.status_label.config(text=status_text))
                            
                            # Update progress
                            current_time = time.strftime("%H:%M:%S")
                            progress_text = f"Last checked: {current_time}"
                            if hasattr(self, 'progress_label'):
                                self.root.after(0, lambda: self.progress_label.config(text=progress_text))
                    
                    time.sleep(2)  # Poll every 2 seconds
                    
                except Exception as e:
                    print(f"Error polling game state: {e}")
                    time.sleep(5)  # Wait longer on error
        
        polling_thread = threading.Thread(target=poll_game_state, daemon=True)
        polling_thread.start()

    async def websocket_listener(self):
        """Listen for WebSocket messages and update UI"""
        try:
            async with websockets.connect(WS_URL) as websocket:
                self.websocket = websocket
                print(f"Connected to WebSocket at {WS_URL}")
                
                # Schedule UI update on main thread
                self.root.after(0, lambda: self.log_message("Connected to game server!"))
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        print("Received WebSocket data:", data)
                        
                        # Handle different message types
                        if data.get("type") == "game_state_update":
                            game_data = data.get("data")
                            if game_data:
                                # Schedule UI update on main thread
                                self.root.after(0, lambda: self.update_game_display(game_data))
                        
                        elif "positions" in data:
                            # Handle position updates from player_engine
                            if self.game_started:
                                # Trigger a game state refresh
                                self.root.after(0, self.request_game_state)
                    
                    except json.JSONDecodeError as e:
                        error_msg = f"Error parsing WebSocket message: {str(e)}"
                        print(error_msg)
                        self.root.after(0, lambda: self.log_message(error_msg))
                        
        except websockets.exceptions.ConnectionClosed:
            error_msg = "WebSocket connection closed"
            print(error_msg)
            self.root.after(0, lambda: self.log_message(error_msg))
        except Exception as e:
            error_msg = f"WebSocket error: {str(e)}"
            print(error_msg)
            self.root.after(0, lambda: self.log_message(error_msg))

if __name__ == "__main__":
    root = tk.Tk()
    app = MonopolyUI(root)
    root.mainloop()
