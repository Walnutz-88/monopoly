import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
import websockets
import json
import os
import argparse
import threading
import requests

# WebSocket URL
WS_URL = "ws://localhost:8000/ws"
API_URL = "http://localhost:8000"

class MonopolyUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Monopoly Game")
        self.root.geometry("800x600")
        self.websocket = None
        self.game_started = False
        
        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Setup UI
        self.setup_start_screen()
        
        # Start WebSocket connection in background
        self.start_websocket_connection()
    
    def setup_start_screen(self):
        """Setup the initial game start screen"""
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Title Label
        self.title_label = ttk.Label(self.main_frame, text="Welcome to Monopoly", font=("Helvetica", 20))
        self.title_label.pack(pady=20)

        # Player selection
        self.player_count_label = ttk.Label(self.main_frame, text="Select Number of Players (2-6):")
        self.player_count_label.pack()

        self.player_count_var = tk.IntVar(value=2)
        self.player_count_spinbox = ttk.Spinbox(self.main_frame, from_=2, to=6, textvariable=self.player_count_var, width=5)
        self.player_count_spinbox.pack(pady=10)

        # Start Button
        self.start_button = ttk.Button(self.main_frame, text="Start Game", command=self.start_game)
        self.start_button.pack(pady=20)
    
    def setup_game_screen(self):
        """Setup the main game screen"""
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Game title
        self.game_title = ttk.Label(self.main_frame, text="Monopoly Game in Progress", font=("Helvetica", 16))
        self.game_title.pack(pady=10)
        
        # Game state display
        self.game_state_frame = ttk.LabelFrame(self.main_frame, text="Game State", padding="10")
        self.game_state_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Current player info
        self.current_player_label = ttk.Label(self.game_state_frame, text="Current Player: -", font=("Helvetica", 12, "bold"))
        self.current_player_label.pack(anchor=tk.W)
        
        # Game status
        self.game_status_label = ttk.Label(self.game_state_frame, text="Game Status: -")
        self.game_status_label.pack(anchor=tk.W)
        
        # Players info
        self.players_frame = ttk.LabelFrame(self.game_state_frame, text="Players", padding="5")
        self.players_frame.pack(fill=tk.X, pady=10)
        
        # Game log
        self.log_frame = ttk.LabelFrame(self.game_state_frame, text="Game Log", padding="5")
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=10, width=70)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=10)
        
        self.reset_button = ttk.Button(self.control_frame, text="Reset Game", command=self.reset_game)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        self.refresh_button = ttk.Button(self.control_frame, text="Refresh", command=self.request_game_state)
        self.refresh_button.pack(side=tk.LEFT, padx=5)

    def start_game(self):
        player_count = self.player_count_var.get()
        print(f"Starting game with {player_count} players")
        
        # Send reset request to backend
        try:
            response = requests.post(f"{API_URL}/reset", json={"num_players": player_count})
            if response.status_code == 200:
                self.game_started = True
                self.setup_game_screen()
                self.log_message(f"Game started with {player_count} players!")
            else:
                self.log_message(f"Failed to start game: {response.text}")
        except Exception as e:
            self.log_message(f"Error starting game: {str(e)}")
    
    def reset_game(self):
        """Reset the game and return to start screen"""
        self.game_started = False
        self.setup_start_screen()
    
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
            # Update current player
            if 'players' in game_data and 'player_turn' in game_data:
                current_player_index = game_data['player_turn']
                if current_player_index < len(game_data['players']):
                    current_player = game_data['players'][current_player_index]
                    self.current_player_label.config(text=f"Current Player: {current_player['name']}")
            
            # Update game status
            game_status = game_data.get('state', 'unknown')
            self.game_status_label.config(text=f"Game Status: {game_status}")
            
            # Update players info
            for widget in self.players_frame.winfo_children():
                widget.destroy()
            
            if 'players' in game_data:
                for i, player in enumerate(game_data['players']):
                    player_info = f"{player['name']}: ${player['money']} (Position: {player['position']})"
                    if i == game_data.get('player_turn', -1):
                        player_info += " [CURRENT TURN]"
                    
                    player_label = ttk.Label(self.players_frame, text=player_info)
                    player_label.pack(anchor=tk.W)
            
            # Log the update
            self.log_message(f"Game state updated - Status: {game_status}")
        
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
                        
                        if data.get("type") == "game_state_update":
                            game_data = data.get("data")
                            if game_data:
                                # Schedule UI update on main thread
                                self.root.after(0, lambda: self.update_game_display(game_data))
                    
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
