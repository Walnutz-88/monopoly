import tkinter as tk
from tkinter import ttk
import asyncio
import websockets
import json
import os
import argparse

# WebSocket URL
WS_URL = "ws://localhost:8000/state"

class MonopolyUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Monopoly Game")

        # Title Label
        self.title_label = ttk.Label(root, text="Welcome to Monopoly", font=("Helvetica", 20))
        self.title_label.pack(pady=20)

        # Player selection
        self.player_count_label = ttk.Label(root, text="Select Number of Players (2-6):")
        self.player_count_label.pack()

        self.player_count_var = tk.IntVar(value=2)
        self.player_count_spinbox = ttk.Spinbox(root, from_=2, to=6, textvariable=self.player_count_var, width=5)
        self.player_count_spinbox.pack(pady=10)

        # Start Button
        self.start_button = ttk.Button(root, text="Start Game", command=self.start_game)
        self.start_button.pack(pady=20)

    def start_game(self):
        player_count = self.player_count_var.get()
        print(f"Starting game with {player_count} players")
        # Here we would normally send the player_count to a backend or use it to configure the game

async def websocket_listener():
    async with websockets.connect(WS_URL) as websocket:
        print(f"Connected to WebSocket at {WS_URL}")
        async for message in websocket:
            data = json.loads(message)
            print("Received data:", data)

if __name__ == "__main__":
    root = tk.Tk()
    app = MonopolyUI(root)
    asyncio.run(websocket_listener())
    root.mainloop()