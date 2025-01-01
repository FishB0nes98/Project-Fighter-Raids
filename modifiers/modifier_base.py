from enum import Enum
from typing import Optional

class ModifierRarity(Enum):
    COMMON = (165, 165, 165)     # Gray
    UNCOMMON = (0, 255, 0)       # Green
    RARE = (0, 0, 255)           # Blue
    EPIC = (128, 0, 128)         # Purple
    LEGENDARY = (255, 165, 0)    # Orange

class Modifier:
    def __init__(self, 
                 name: str,
                 description: str,
                 rarity: ModifierRarity,
                 image_path: Optional[str] = None):
        self.name = name
        self.description = description
        self.rarity = rarity
        self.image_path = image_path
        self.is_active = False
        print(f"Created modifier: {name} with rarity {rarity.name}")

    def activate(self):
        """Called when the modifier is chosen and activated"""
        self.is_active = True
        print(f"Activated modifier: {self.name}")

    def on_turn_start(self, game_state):
        """Called at the start of each turn"""
        pass

    def on_turn_end(self, game_state):
        """Called at the end of each turn"""
        pass

    def on_battle_start(self, game_state):
        """Called when a battle starts"""
        pass

    def on_battle_end(self, game_state):
        """Called when a battle ends"""
        pass 