from typing import List, Optional, Dict, Type
import pygame
from characters.base_character import Character
from pathlib import Path
from items.loot_table import LootTable
from PIL import Image

# Global cache for stage backgrounds to share between stages
_background_cache: Dict[str, pygame.Surface] = {}

class BaseStage:
    def __init__(self, 
                 stage_number: int,
                 name: str,
                 description: str,
                 background_path: str):
        self.stage_number = stage_number
        self.name = name
        self.description = description
        self.bosses: List[Character] = []
        self.completed = False
        
        # Load and cache background with high quality scaling
        if background_path not in _background_cache:
            # Load image with PIL for high quality scaling
            pil_image = Image.open(str(Path(background_path)))
            pil_image = pil_image.convert('RGB')  # Use RGB instead of RGBA for backgrounds
            pil_image = pil_image.resize((1920, 1080), Image.Resampling.LANCZOS)
            
            # Convert to Pygame surface and optimize for display
            image_data = pil_image.tobytes()
            pygame_image = pygame.image.fromstring(image_data, pil_image.size, 'RGB')
            pygame_image = pygame_image.convert()  # Convert to display format for faster blitting
            
            # Cache the optimized image
            _background_cache[background_path] = pygame_image
        
        # Use cached background
        self.background = _background_cache[background_path]
        
        # Loot tables for each enemy type
        self.loot_tables: Dict[Type[Character], LootTable] = {}
    
    @staticmethod
    def clear_background_cache():
        """Clear the background cache."""
        _background_cache.clear()
    
    def add_loot_table(self, character_class: Type[Character], loot_table: LootTable):
        """Add a loot table for a specific character class."""
        print(f"Adding loot table for character class: {character_class}")
        self.loot_tables[character_class] = loot_table
    
    def get_loot_table(self, character) -> Optional[LootTable]:
        """Get the loot table for a character type."""
        # Get character name for logging
        char_name = character.name if hasattr(character, 'name') else character.__name__
        print(f"\nLooking up loot table for character: {char_name}")
        
        # Get character type
        char_type = character if isinstance(character, type) else type(character)
        print(f"Character type: {char_type}")
        print(f"Available loot tables for types: {list(self.loot_tables.keys())}")
        
        # Check if we have a loot table for this character type
        found = char_type in self.loot_tables
        print(f"Found loot table: {found}")
        
        if found:
            print(f"Found loot table: {self.loot_tables[char_type]}")
            return self.loot_tables[char_type]
        return None
    
    def setup_bosses(self) -> List[Character]:
        """Override this method to define stage-specific bosses"""
        raise NotImplementedError("Each stage must implement setup_bosses")
    
    def initialize(self):
        """Initialize the stage, setting up bosses and any stage-specific mechanics"""
        self.bosses = self.setup_bosses()
    
    def is_completed(self) -> bool:
        return all(not boss.is_alive() for boss in self.bosses)
    
    def update(self):
        """Update stage-specific mechanics. Override if needed."""
        for boss in self.bosses:
            boss.update()
    
    def draw(self, screen: pygame.Surface):
        """Base draw method that draws the background."""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Draw bosses
        for boss in self.bosses:
            boss.draw(screen)
    
    def on_enter(self):
        """Called when the stage is entered. Override if needed."""
        pass
    
    def on_exit(self):
        """Called when the stage is completed. Override if needed."""
        pass 