"""Raid inventory management."""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from services.database_service import DatabaseService
from config.login_config import LoginManager
from items.base_item import Item
from items.consumables import (
    MurkyWaterVial, DeepSeaEssence, IceShard, IceDagger, IceFlask, 
    PiranhaTooth, SmokeBomb, LeviathanMistVial, AbyssalEcho, AtlanteanTrident,
    ManaPotion, CursedWaterVial, UnderwaterCursedShell
)
from items.buffs import PiranhaScales, TidalCharm, VoidEssence, ShadowDagger
from items.legendary_items import IceBlade, ZasalamelsScythe
from items.crafting_materials import ShadowEssence, LeviathanScale

# Item class mapping
ITEM_CLASSES = {
    "Murky Water Vial": MurkyWaterVial,
    "Deep Sea Essence": DeepSeaEssence,
    "Piranha Scales": PiranhaScales,
    "Piranha Tooth": PiranhaTooth,
    "Smoke Bomb": SmokeBomb,
    "Tidal Charm": TidalCharm,
    "Void Essence": VoidEssence,
    "Ice Blade": IceBlade,
    "Ice Shard": IceShard,
    "Ice Dagger": IceDagger,
    "Ice Flask": IceFlask,
    "Shadow Essence": ShadowEssence,
    "Shadow Dagger": ShadowDagger,
    "Leviathan Scale": LeviathanScale,
    "Leviathan's Mist Vial": LeviathanMistVial,
    "Abyssal Echo": AbyssalEcho,
    "Atlantean Trident of Time Manipulation": AtlanteanTrident,
    "Mana Potion": ManaPotion,
    "Zasalamel's Scythe": ZasalamelsScythe,
    "Cursed Water Vial": CursedWaterVial,
    "Underwater Cursed Shell": UnderwaterCursedShell
}

class RaidInventory:
    MAX_ITEMS = 6  # Maximum number of different items that can be held
    
    def __init__(self):
        """Initialize the raid inventory."""
        self.login_manager = LoginManager()
        credentials = self.login_manager.load_credentials()
        self.username = credentials[0] if credentials else "default_user"
        self.db_service = DatabaseService()
        self.user_id = self.db_service.user_id  # Get user_id from DatabaseService
        
        self.inventory: Dict[str, int] = {}  # {item_name: count}
        self.modifiers: Dict[str, Dict[int, list]] = {}  # {raid_type: {stage: [modifiers]}}
        self.currency: Dict[str, int] = {
            "gold": 0,
            "raid_tokens": 0,
            "void_essence": 0
        }
        
        # Initialize empty inventories and default currencies
        self.items = {}  # Active inventory (max 6 slots)
        self.global_inventory = {}  # Global inventory for overflow items
        self.currencies = {
            "cm": 1000,
            "fm": 200
        }
        
        # Initialize modifiers with stage-specific keys
        self.active_modifiers = {
            "atlantean_raid_stage1": [],  # Stage 1 modifiers
            "atlantean_raid_stage2": [],  # Stage 2 modifiers
            "atlantean_raid_stage3": [],  # Stage 3 modifiers
            "atlantean_raid_stage4": [],  # Stage 4 modifiers
            "atlantean_raid_stage5": []   # Stage 5 modifiers
        }
        
        # Ensure Raidfolder exists
        self.raid_folder = Path("Raidfolder")
        self.raid_folder.mkdir(exist_ok=True)
        
        # Load saved inventory
        self.load_inventory()
        print(f"Initial active items loaded: {self.items}")  # Debug print
        print(f"Initial global items loaded: {self.global_inventory}")  # Debug print
        print(f"Initial currencies loaded: {self.currencies}")  # Debug print
        print(f"Initial active modifiers loaded: {self.active_modifiers}")  # Debug print
    
    def save_inventory(self):
        """Save the current inventory state."""
        # Save to local file
        inventory_data = {
            "items": self.items,
            "global_inventory": self.global_inventory,
            "currencies": self.currencies,
            "active_modifiers": self.active_modifiers
        }
        
        with open(self.raid_folder / "inventory.json", "w") as f:
            json.dump(inventory_data, f, indent=2)
            
        # Save to Firebase
        print(f"Saving to Firebase for user: {self.user_id}")  # Debug print
        print(f"Current active items: {self.items}")  # Debug print
        print(f"Current global items: {self.global_inventory}")  # Debug print
        print(f"Current currencies: {self.currencies}")  # Debug print
        print(f"Current active modifiers: {self.active_modifiers}")  # Debug print
        
        try:
            # Prepare data in the exact format matching the database
            data = {
                "RaidInventory": {
                    "items": self.items,
                    "currencies": self.currencies,
                    "active_modifiers": self.active_modifiers
                }
            }
            
            # If there are items in global inventory, merge them with items
            if self.global_inventory:
                for item_name, count in self.global_inventory.items():
                    if item_name in data["RaidInventory"]["items"]:
                        data["RaidInventory"]["items"][item_name] += count
                    else:
                        data["RaidInventory"]["items"][item_name] = count
            
            self.db_service.save_player_data(self.user_id, data)
            print("Successfully saved inventory to Firebase")
        except Exception as e:
            print(f"Error saving to Firebase: {e}")
    
    def load_inventory(self):
        """Load the inventory state."""
        print(f"\nLoading from Firebase for user: {self.user_id}")  # Debug print
        
        # Try to load from Firebase first
        try:
            data = self.db_service.get_player_data(self.user_id)
            print(f"Loaded user data: {data}")  # Debug print
            
            if data and "RaidInventory" in data:
                raid_data = data["RaidInventory"]
                print(f"Loaded raid data: {raid_data}")  # Debug print
                
                # Load items directly without normalization
                if "items" in raid_data:
                    self.items = raid_data["items"]
                    print(f"Loaded items: {self.items}")  # Debug print
                
                # Load global inventory directly without normalization
                if "global_inventory" in raid_data:
                    self.global_inventory = raid_data.get("global_inventory", {})
                    print(f"Loaded global items: {self.global_inventory}")  # Debug print
                
                if "currencies" in raid_data:
                    self.currencies = raid_data["currencies"]
                    print(f"Loaded currencies: {self.currencies}")  # Debug print
                    
                if "active_modifiers" in raid_data:
                    loaded_modifiers = raid_data["active_modifiers"]
                    print(f"\nLoaded modifiers from database: {loaded_modifiers}")
                    # Ensure we have stage-specific keys
                    if isinstance(loaded_modifiers, dict):
                        # Convert old format if needed
                        if "atlantean_raid" in loaded_modifiers:
                            print("Converting old format modifiers to stage-specific format")
                            # Move old modifiers to stage 1
                            self.active_modifiers = {
                                "atlantean_raid_stage1": loaded_modifiers["atlantean_raid"],
                                "atlantean_raid_stage2": [],
                                "atlantean_raid_stage3": [],
                                "atlantean_raid_stage4": [],
                                "atlantean_raid_stage5": []
                            }
                        else:
                            print("Loading stage-specific modifiers")
                            # Use loaded modifiers with default empty lists for missing stages
                            self.active_modifiers = {
                                "atlantean_raid_stage1": loaded_modifiers.get("atlantean_raid_stage1", []),
                                "atlantean_raid_stage2": loaded_modifiers.get("atlantean_raid_stage2", []),
                                "atlantean_raid_stage3": loaded_modifiers.get("atlantean_raid_stage3", []),
                                "atlantean_raid_stage4": loaded_modifiers.get("atlantean_raid_stage4", []),
                                "atlantean_raid_stage5": loaded_modifiers.get("atlantean_raid_stage5", [])
                            }
                    else:
                        print("Invalid modifier format, initializing empty")
                        # Initialize with empty lists if format is invalid
                        self.active_modifiers = {
                            "atlantean_raid_stage1": [],
                            "atlantean_raid_stage2": [],
                            "atlantean_raid_stage3": [],
                            "atlantean_raid_stage4": [],
                            "atlantean_raid_stage5": []
                        }
                    print(f"Final active modifiers state: {self.active_modifiers}")  # Debug print
            else:
                print("First time loading, saving initial state")
                self.save_inventory()
                
        except Exception as e:
            print(f"Error loading from Firebase: {e}")
            
            # Fall back to local file if Firebase fails
            try:
                if (self.raid_folder / "inventory.json").exists():
                    with open(self.raid_folder / "inventory.json", "r") as f:
                        data = json.load(f)
                        self.items = data.get("items", {})
                        self.global_inventory = data.get("global_inventory", {})
                        self.currencies = data.get("currencies", self.currencies)
                        loaded_modifiers = data.get("active_modifiers", {})
                        # Ensure we have stage-specific keys
                        if "atlantean_raid" in loaded_modifiers:
                            # Move old modifiers to stage 1
                            self.active_modifiers = {
                                "atlantean_raid_stage1": loaded_modifiers["atlantean_raid"],
                                "atlantean_raid_stage2": [],
                                "atlantean_raid_stage3": [],
                                "atlantean_raid_stage4": [],
                                "atlantean_raid_stage5": []
                            }
                        else:
                            self.active_modifiers = {
                                "atlantean_raid_stage1": loaded_modifiers.get("atlantean_raid_stage1", []),
                                "atlantean_raid_stage2": loaded_modifiers.get("atlantean_raid_stage2", []),
                                "atlantean_raid_stage3": loaded_modifiers.get("atlantean_raid_stage3", []),
                                "atlantean_raid_stage4": loaded_modifiers.get("atlantean_raid_stage4", []),
                                "atlantean_raid_stage5": loaded_modifiers.get("atlantean_raid_stage5", [])
                            }
            except Exception as e:
                print(f"Error loading from local file: {e}")
    
    def add_modifier(self, raid_type: str, modifier_name: str, stage: int):
        """Add a modifier to the specified raid type and stage."""
        key = f"{raid_type}_stage{stage}"
        print(f"\nAdding modifier {modifier_name} to {key}")
        if key not in self.active_modifiers:
            print(f"Creating new list for {key}")
            self.active_modifiers[key] = []
        if modifier_name not in self.active_modifiers[key]:
            print(f"Adding {modifier_name} to {key}")
            self.active_modifiers[key].append(modifier_name)
            print(f"Current modifiers for {key}: {self.active_modifiers[key]}")
            self.save_inventory()
            
    def clear_modifiers(self, raid_type: str, stage: int):
        """Clear all modifiers for the specified raid type and stage."""
        key = f"{raid_type}_stage{stage}"
        print(f"\nClearing modifiers for {key}")
        if key in self.active_modifiers:
            print(f"Before clear: {self.active_modifiers[key]}")
            self.active_modifiers[key] = []
            print(f"After clear: {self.active_modifiers[key]}")
            self.save_inventory()
            
    def get_modifiers(self, raid_type: str, stage: int) -> list:
        """Get all active modifiers for the specified raid type and stage."""
        key = f"{raid_type}_stage{stage}"
        print(f"\nGetting modifiers for {key}")
        modifiers = self.active_modifiers.get(key, [])
        print(f"Found modifiers: {modifiers}")
        return modifiers
    
    def can_add_item(self, item_name: str) -> bool:
        """Check if an item can be added to the inventory."""
        # If the item already exists in active inventory, we can always add more
        if item_name in self.items:
            return True
        # Otherwise, check if we have room for a new item type
        return len(self.items) < self.MAX_ITEMS
    
    def add_item(self, item_name: str, amount: int = 1) -> bool:
        """Add an item to the inventory.
        
        Returns:
            bool: True if the item was added successfully
        """
        print(f"\n[DEBUG] Adding {amount} {item_name} to inventory")  # Debug print
        print(f"[DEBUG] Current items: {self.items}")  # Debug print
        print(f"[DEBUG] Current global inventory: {self.global_inventory}")  # Debug print
        
        # Check if item exists in active inventory
        if item_name in self.items:
            self.items[item_name] += amount
            print(f"[DEBUG] Added {amount} {item_name} to active inventory (existing stack)")  # Debug print
            self.save_inventory()
            return True
            
        # If not in active inventory and we have space, add it
        if len(self.items) < self.MAX_ITEMS:
            self.items[item_name] = amount
            print(f"[DEBUG] Added {amount} {item_name} to active inventory (new stack)")  # Debug print
            self.save_inventory()
            return True
            
        # Add to global inventory if active inventory is full
        if item_name not in self.global_inventory:
            self.global_inventory[item_name] = 0
        self.global_inventory[item_name] += amount
        print(f"[DEBUG] Added {amount} {item_name} to global inventory (active inventory full)")  # Debug print
        
        # Save to database and refresh
        self.save_inventory()
        self.load_inventory()  # Refresh from database to ensure consistency
        
        return True
    
    def remove_item(self, item_name: str, amount: int = 1) -> bool:
        """Remove an item from the inventory.
        
        Checks both active and global inventory.
        Returns:
            bool: True if the item was removed successfully, False if not enough items
        """
        print(f"\n[DEBUG] Attempting to remove {amount} {item_name}")  # Debug print
        print(f"[DEBUG] Current items: {self.items}")  # Debug print
        print(f"[DEBUG] Current global inventory: {self.global_inventory}")  # Debug print
        
        # Use exact item name without normalization
        if item_name in self.items:
            print(f"[DEBUG] Found item in active inventory with count: {self.items[item_name]}")  # Debug print
            if self.items[item_name] >= amount:
                self.items[item_name] -= amount
                print(f"[DEBUG] Removed {amount}, new count: {self.items[item_name]}")  # Debug print
                if self.items[item_name] <= 0:
                    del self.items[item_name]
                    print(f"[DEBUG] Count zero, removed item from inventory")  # Debug print
                self.save_inventory()
                return True
            else:
                remaining = amount - self.items[item_name]
                del self.items[item_name]
                print(f"[DEBUG] Not enough in active inventory, checking global for remaining {remaining}")  # Debug print
                # Try to remove remaining amount from global inventory
                if item_name in self.global_inventory and self.global_inventory[item_name] >= remaining:
                    self.global_inventory[item_name] -= remaining
                    if self.global_inventory[item_name] <= 0:
                        del self.global_inventory[item_name]
                    self.save_inventory()
                    return True
                return False
        
        # If not in active inventory, try global inventory
        if item_name in self.global_inventory:
            print(f"[DEBUG] Found item in global inventory with count: {self.global_inventory[item_name]}")  # Debug print
            if self.global_inventory[item_name] >= amount:
                self.global_inventory[item_name] -= amount
                print(f"[DEBUG] Removed {amount}, new count: {self.global_inventory[item_name]}")  # Debug print
                if self.global_inventory[item_name] <= 0:
                    del self.global_inventory[item_name]
                    print(f"[DEBUG] Count zero, removed item from global inventory")  # Debug print
                self.save_inventory()
                return True
        
        print(f"[DEBUG] Item not found in either inventory")  # Debug print
        return False
    
    def get_item_count(self, item_name: str) -> int:
        """Get the total count of a specific item across both inventories."""
        normalized_name = " ".join(word.capitalize() for word in item_name.replace("_", " ").split())
        active_count = self.items.get(normalized_name, 0)
        global_count = self.global_inventory.get(normalized_name, 0)
        return active_count + global_count
    
    def get_inventory_space(self) -> int:
        """Get the number of available inventory slots in the active inventory."""
        return self.MAX_ITEMS - len(self.items)
    
    def is_inventory_full(self) -> bool:
        """Check if the active inventory is full."""
        return len(self.items) >= self.MAX_ITEMS
    
    def add_currency(self, currency_type: str, amount: int):
        """Add currency to the inventory."""
        if currency_type in self.currencies:
            self.currencies[currency_type] += amount
            self.save_inventory()
    
    def remove_currency(self, currency_type: str, amount: int) -> bool:
        """Remove currency from the inventory.
        
        Returns:
            bool: True if the currency was removed successfully, False if not enough currency
        """
        if currency_type not in self.currencies or self.currencies[currency_type] < amount:
            return False
            
        self.currencies[currency_type] -= amount
        self.save_inventory()
        return True
    
    def get_currency(self, currency_type: str) -> int:
        """Get the amount of a specific currency."""
        return self.currencies.get(currency_type, 0) 
    
    def create_item_object(self, item_name: str, count: int = 1) -> Optional[Item]:
        """Create an Item object from the item name."""
        if item_name in ITEM_CLASSES:
            item = ITEM_CLASSES[item_name]()
            item.stack_count = count
            return item
        print(f"Warning: Unknown item type {item_name}")
        return None

    def populate_ui_inventory(self, inventory):
        """Populate a UI inventory with the current items."""
        print("\nPopulating UI inventory...")
        
        # Clear inventory first
        inventory.slots = [None] * 6
        
        # Add items to inventory
        slot_index = 0
        for item_name, count in self.items.items():
            print(f"Processing item: {item_name} (count: {count})")
            if item_name in ITEM_CLASSES:
                item_class = ITEM_CLASSES[item_name]
                print(f"Found item class: {item_class.__name__}")
                try:
                    # Create item instance
                    item = item_class()
                    item.stack_count = count
                    if slot_index < len(inventory.slots):
                        inventory.slots[slot_index] = item
                        slot_index += 1
                        print(f"Added {item.name} to slot {slot_index-1}")
                    else:
                        print(f"No more slots available for {item_name}")
                except Exception as e:
                    print(f"Error creating item {item_name}: {str(e)}")
            else:
                print(f"Warning: Unknown item type {item_name}")
        
        print("UI inventory population complete\n") 