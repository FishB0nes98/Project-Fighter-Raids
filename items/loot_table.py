from typing import List, Dict, Optional
from dataclasses import dataclass
import random

@dataclass
class LootEntry:
    item_class: type  # The class of the item to create
    chance: float  # Drop chance as a percentage (0-100)
    min_count: int = 1  # Minimum number of items to drop
    max_count: int = 1  # Maximum number of items to drop

class LootTable:
    def __init__(self, min_total_drops: int = 0, max_total_drops: int = 1):
        self.entries: List[LootEntry] = []
        self.min_total_drops = min_total_drops
        self.max_total_drops = max_total_drops
    
    def add_entry(self, item_class: type, chance: float, min_count: int = 1, max_count: int = 1):
        """Add an item to the loot table with its drop chance and count range."""
        self.entries.append(LootEntry(item_class, chance, min_count, max_count))
    
    def roll_loot(self) -> List:
        """Roll for loot drops and return a list of instantiated items."""
        print("\nRolling for loot...")
        print(f"Min drops: {self.min_total_drops}, Max drops: {self.max_total_drops}")
        potential_drops = []
        
        # First, roll for each entry
        for entry in self.entries:
            roll = random.random() * 100
            print(f"Rolling for {entry.item_class.__name__}: {roll:.2f} vs {entry.chance}% chance")
            if roll < entry.chance:
                # Determine how many to drop
                count = random.randint(entry.min_count, entry.max_count)
                print(f"Success! Rolling {count} {entry.item_class.__name__}(s)")
                for _ in range(count):
                    potential_drops.append(entry.item_class())
        
        print(f"Total potential drops: {len(potential_drops)}")
        
        # If we have more potential drops than max_total_drops, randomly select max_total_drops items
        if len(potential_drops) > self.max_total_drops:
            print(f"Too many drops ({len(potential_drops)}), reducing to {self.max_total_drops}")
            random.shuffle(potential_drops)
            potential_drops = potential_drops[:self.max_total_drops]
        
        # If we have fewer drops than min_total_drops, add random items until we reach min_total_drops
        while len(potential_drops) < self.min_total_drops and self.entries:
            print(f"Too few drops ({len(potential_drops)}), adding random item to reach minimum {self.min_total_drops}")
            # Pick a random entry and create an item
            entry = random.choice(self.entries)
            potential_drops.append(entry.item_class())
        
        print(f"Final drops: {[type(item).__name__ for item in potential_drops]}\n")
        return potential_drops 