import os
import sys

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.game_engine import GameEngine
from gui.login_window import LoginWindow

if __name__ == "__main__":
    # Show login window first
    login_window = LoginWindow()
    username, password = login_window.run()
    
    if username and password:  # Only start game if login successful
        game = GameEngine()
        game.run() 