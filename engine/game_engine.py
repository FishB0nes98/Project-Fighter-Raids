import pygame
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from characters.base_character import Character
from engine.stage_manager import StageManager
from characters.atlantean_kagome import create_atlantean_kagome
from characters.subzero import create_subzero
from stages.stage_1 import Stage1
from stages.stage_2 import Stage2
from stages.stage_3 import Stage3
from stages.stage_4 import Stage4
from stages.stage_5 import Stage5
from stages.stage_6 import Stage6
from ui.battle_log import BattleLog
from ui.inventory import Inventory
import math
from abilities.base_ability import Ability
from effects.visual_effects import VisualEffectManager
from ui.loot_window import LootWindow
from services.database_service import DatabaseService
from characters.shadowfin_boss import Piranha
from items.raid_inventory import RaidInventory
from ui.modifier_selection import ModifierSelectionWindow
from modifiers.modifier_manager import ModifierManager
import uuid
from ui.active_modifiers_display import ActiveModifiersDisplay
from ui.stage_selector import StageSelector
from PIL import Image
import os
from engine.action_queue import ActionQueue

# Global image cache
_image_cache: Dict[Tuple[str, Optional[Tuple[int, int]]], pygame.Surface] = {}

@dataclass
class GameState:
    current_stage: int = 1
    is_player_turn: bool = True
    selected_ability: Optional[int] = None
    selected_target: Optional[int] = None
    turn_count: int = 1
    target_highlight_time: float = 0  # For pulsing effect
    boss_action_timer: float = 0  # Timer for boss action delay
    current_acting_boss: int = 0  # Index of current boss taking action
    targeting_item: bool = False  # Whether we're targeting for an item use
    show_modifier_selection: bool = True  # Whether to show modifier selection
    selected_character_index: int = 0  # Index of currently selected character

class GameEngine:
    # Colors
    BG_COLOR = (40, 44, 52)  # Dark background
    TURN_BG_COLOR = (48, 52, 64)
    TURN_BORDER_COLOR = (80, 84, 96)
    TURN_TEXT_COLOR = (220, 220, 220)
    TARGET_HIGHLIGHT_COLOR = (255, 215, 0, 100)  # Semi-transparent gold
    
    instance = None  # Class variable to store singleton instance
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        GameEngine.instance = self  # Store instance reference
        pygame.init()
        self.screen_width = screen_width  # Store as instance variable
        self.screen_height = screen_height  # Store as instance variable
        self.screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption("Project Fighter Raids")
        self.clock = pygame.time.Clock()
        self.game_state = GameState()
        self.running = True
        
        # Initialize database service first
        self.db_service = DatabaseService()
        
        # Initialize raid inventory after database service
        self.raid_inventory = RaidInventory()
        print("Loading raid inventory...")  # Debug print
        
        # Initialize stage manager
        self.stage_manager = StageManager()
        
        # Initialize modifier manager and selection window
        self.modifier_manager = ModifierManager()
        self.modifier_selection = ModifierSelectionWindow(screen_width, screen_height)
        
        # Initialize stage selector
        self.stage_selector = StageSelector(screen_width, screen_height)
        
        self.setup_game()
        
        # Turn counter font
        self.turn_font = pygame.font.Font(None, 36)
        
        # Create target highlight surface
        self.target_surface = pygame.Surface((300, 400), pygame.SRCALPHA)
        
        # Create battle log
        self.battle_log = BattleLog(20, screen_height - 320)  # Position at bottom left
        
        # Create inventory (positioned above characters)
        self.inventory = Inventory(screen_width - 320, 200)  # Position at mid-right
        
        # Populate inventory with raid items
        self.raid_inventory.populate_ui_inventory(self.inventory)
        
        # Target hover state
        self.hovered_target = None
        
        # Colors for target indicators
        self.VALID_TARGET_COLOR = (0, 255, 0, 100)  # Semi-transparent green
        self.HOVERED_TARGET_COLOR = (255, 255, 0, 150)  # Semi-transparent yellow
        
        # Initialize visual effects manager
        self.visual_effects = VisualEffectManager()
        
        # Add loot window
        self.loot_window = LootWindow(710, 140)  # Position in center of screen
        self.pending_loot = []
        
        # Import DebugConsole here to avoid circular import
        from ui.debug_console import DebugConsole
        self.debug_console = DebugConsole(width=800)
        
        # Generate unique player ID
        self.player_id = str(uuid.uuid4())  # Generate unique player ID
        
        # Load saved game state if it exists
        # saved_state = self.db_service.get_game_state(self.player_id)
        # if saved_state:
        #     self.load_game_state(saved_state)
        
        # Add active modifiers display
        self.active_modifiers_display = ActiveModifiersDisplay(self.screen_width)
        
        self.action_queue = ActionQueue()
    
    def setup_game(self):
        """Initialize game state and stages"""
        # Create player characters
        kagome = create_atlantean_kagome()
        
        # Initialize inventory for player character
        from ui.inventory import Inventory
        kagome.inventory = Inventory(x=50, y=200)  # Position at mid-left
        
        self.stage_manager.set_player_characters([kagome])
        
        # Create and add stages
        stage1 = Stage1()
        stage2 = Stage2()
        stage3 = Stage3()
        stage4 = Stage4()
        stage5 = Stage5()
        stage6 = Stage6()
        self.stage_manager.add_stage(stage1)
        self.stage_manager.add_stage(stage2)
        self.stage_manager.add_stage(stage3)
        self.stage_manager.add_stage(stage4)
        self.stage_manager.add_stage(stage5)
        self.stage_manager.add_stage(stage6)
        
        # Show stage selector instead of starting stage 1 directly
        self.stage_selector.show(self.stage_manager.stages, self.on_stage_selected)
    
    def on_stage_selected(self, stage_number: int):
        """Handle stage selection"""
        
        # Hide stage selector
        self.stage_selector.hide()
        
        # Clear all image caches before loading new stage
        self.clear_image_cache()
        from stages.base_stage import BaseStage
        BaseStage.clear_background_cache()
        
        self.game_state.current_stage = stage_number
        
        # Show loading screen and pre-cache assets
        self.show_loading_screen()
        self.pre_cache_stage_assets(stage_number)
        
        # Switch player character based on stage
        if stage_number == 3:
            subzero = create_subzero()
            subzero.inventory = Inventory(x=50, y=200)  # Position at mid-left
            self.stage_manager.set_player_characters([subzero])
        elif stage_number == 4:
            from stages.stage_4 import create_atlantean_christie
            christie = create_atlantean_christie()
            christie.inventory = Inventory(x=50, y=200)  # Position at mid-left
            self.stage_manager.set_player_characters([christie])
        elif stage_number == 5:
            # Set up Sub Zero and Kotal Kahn for Stage 5
            subzero = create_subzero()
            from characters.atlantean_kotal_kahn import create_atlantean_kotal_kahn
            kotal = create_atlantean_kotal_kahn()
            
            # Initialize inventories
            subzero.inventory = Inventory(x=50, y=200)
            kotal.inventory = Inventory(x=50, y=300)
            
            self.stage_manager.set_player_characters([subzero, kotal])
        elif stage_number == 6:
            # Set up all three characters for Stage 6
            subzero = create_subzero()
            from characters.atlantean_kotal_kahn import create_atlantean_kotal_kahn
            kotal = create_atlantean_kotal_kahn()
            kagome = create_atlantean_kagome()
            
            # Initialize inventories
            subzero.inventory = Inventory(x=50, y=200)
            kotal.inventory = Inventory(x=50, y=300)
            kagome.inventory = Inventory(x=50, y=400)
            
            self.stage_manager.set_player_characters([subzero, kotal, kagome])
        else:
            kagome = create_atlantean_kagome()
            kagome.inventory = Inventory(x=50, y=200)  # Position at mid-left
            self.stage_manager.set_player_characters([kagome])
        
        self.stage_manager.start_stage(stage_number)
        # Show modifier selection after stage is selected
        self.show_modifier_selection()
    
    def show_loading_screen(self):
        """Show a loading screen while assets are being cached."""
        # Create loading screen surface
        loading_surface = pygame.Surface((self.screen_width, self.screen_height))
        loading_surface.fill((18, 18, 24))  # Dark background
        
        # Create loading text with glow effect
        loading_font = pygame.font.Font(None, 48)
        loading_text = loading_font.render("Loading", True, (240, 240, 240))
        text_rect = loading_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 50))
        
        # Create glow effect for text
        glow_surface = pygame.Surface((loading_text.get_width() + 20, loading_text.get_height() + 20), pygame.SRCALPHA)
        glow_color = (64, 156, 255, 30)  # Light blue with transparency
        pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect(), border_radius=10)
        
        # Create progress bar background with modern style
        bar_width = 400
        bar_height = 8  # Thinner bar
        bar_rect = pygame.Rect(
            (self.screen_width - bar_width) // 2,
            self.screen_height // 2 + 20,
            bar_width,
            bar_height
        )
        
        # Create status text
        status_font = pygame.font.Font(None, 24)
        status_text = status_font.render("Preparing assets...", True, (185, 185, 195))
        status_rect = status_text.get_rect(center=(self.screen_width // 2, bar_rect.bottom + 25))
        
        # Draw initial loading screen
        # Draw text glow
        loading_surface.blit(glow_surface, 
                           (text_rect.x - 10, text_rect.y - 10))
        # Draw text
        loading_surface.blit(loading_text, text_rect)
        
        # Draw progress bar background with rounded corners
        pygame.draw.rect(loading_surface, (32, 36, 44), bar_rect, border_radius=4)
        pygame.draw.rect(loading_surface, (44, 48, 56), bar_rect, width=1, border_radius=4)
        
        # Draw status text
        loading_surface.blit(status_text, status_rect)
        
        self.screen.blit(loading_surface, (0, 0))
        pygame.display.flip()
        
        self._loading_surface = loading_surface
        self._loading_bar_rect = bar_rect
        self._status_font = status_font
        self._loading_text = loading_text
        self._text_rect = text_rect
        self._dots_timer = 0
        self._dots_count = 0
    
    def update_loading_progress(self, progress: float, status: str = ""):
        """Update the loading screen progress bar."""
        # Clear the previous progress and status
        clear_rect = pygame.Rect(
            0,
            self._text_rect.y - 10,
            self.screen_width,
            self._loading_bar_rect.bottom + 50
        )
        pygame.draw.rect(self._loading_surface, (18, 18, 24), clear_rect)
        
        # Update loading text animation
        self._dots_timer += 1
        if self._dots_timer >= 30:  # Change dots every 30 frames
            self._dots_timer = 0
            self._dots_count = (self._dots_count + 1) % 4
        
        # Draw animated loading text with dots
        dots = "." * self._dots_count
        loading_text = self._loading_text.copy()
        dots_surface = self._status_font.render(dots, True, (240, 240, 240))
        dots_rect = dots_surface.get_rect(midleft=(self._text_rect.right + 5, self._text_rect.centery))
        
        # Draw text and dots
        self._loading_surface.blit(loading_text, self._text_rect)
        self._loading_surface.blit(dots_surface, dots_rect)
        
        # Draw progress bar background
        pygame.draw.rect(self._loading_surface, (32, 36, 44), self._loading_bar_rect, border_radius=4)
        
        # Draw progress bar fill with gradient effect
        if progress > 0:
            fill_rect = self._loading_bar_rect.copy()
            fill_rect.width = int(self._loading_bar_rect.width * progress)
            if fill_rect.width > 0:
                # Create gradient effect
                gradient_rect = fill_rect.copy()
                gradient_surface = pygame.Surface((gradient_rect.width, gradient_rect.height), pygame.SRCALPHA)
                
                # Define gradient colors (from darker to lighter blue)
                start_color = (48, 128, 255)
                end_color = (64, 156, 255)
                
                for x in range(gradient_rect.width):
                    progress = x / gradient_rect.width
                    current_color = [
                        int(start_color[i] + (end_color[i] - start_color[i]) * progress)
                        for i in range(3)
                    ]
                    pygame.draw.line(gradient_surface, (*current_color, 255), 
                                   (x, 0), (x, gradient_rect.height))
                
                # Apply gradient
                self._loading_surface.blit(gradient_surface, gradient_rect)
                
                # Add subtle glow effect
                glow_surface = pygame.Surface((fill_rect.width + 10, fill_rect.height + 10), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (*end_color, 30), 
                               glow_surface.get_rect(), border_radius=6)
                self._loading_surface.blit(glow_surface, 
                                         (fill_rect.x - 5, fill_rect.y - 5))
        
        # Draw progress bar border
        pygame.draw.rect(self._loading_surface, (44, 48, 56), self._loading_bar_rect, width=1, border_radius=4)
        
        # Draw status text
        if status:
            status_text = self._status_font.render(status, True, (185, 185, 195))
            status_rect = status_text.get_rect(center=(self.screen_width // 2, self._loading_bar_rect.bottom + 25))
            self._loading_surface.blit(status_text, status_rect)
        
        # Update screen
        self.screen.blit(self._loading_surface, (0, 0))
        pygame.display.flip()
        
        # Process events to prevent "not responding"
        pygame.event.pump()
    
    def pre_cache_stage_assets(self, stage_number: int):
        """Pre-cache assets for the selected stage."""
        from PIL import Image
        import os
        
        def cache_image(path: str, size: tuple = None, asset_name: str = None) -> pygame.Surface:
            """Helper function to cache a single image with optional resizing."""
            # Use both path and asset name in cache key for unique identification
            cache_key = (path, size, asset_name) if asset_name else (path, size)
            
            if cache_key in _image_cache:
                return _image_cache[cache_key]
            
            if not os.path.exists(path):
                print(f"Warning: Image not found: {path}")
                return None
            
            try:
                # Convert image to RGB mode if it's not already
                with Image.open(path) as pil_image:
                    if pil_image.mode == 'RGBA':
                        pil_image = pil_image.convert('RGBA')
                    else:
                        pil_image = pil_image.convert('RGB')
                    
                    if size:
                        # Use box sampling for downscaling (faster and less memory intensive)
                        if (pil_image.size[0] > size[0] or pil_image.size[1] > size[1]):
                            pil_image = pil_image.resize(size, Image.Resampling.BOX)
                        else:
                            # Use LANCZOS only for upscaling
                            pil_image = pil_image.resize(size, Image.Resampling.LANCZOS)
                    
                    # Convert to pygame surface efficiently
                    mode = 'RGBA' if pil_image.mode == 'RGBA' else 'RGB'
                    image_data = pil_image.tobytes()
                    surface = pygame.image.fromstring(image_data, pil_image.size, mode)
                    
                    # Convert surface to display format for faster blitting
                    surface = surface.convert_alpha() if mode == 'RGBA' else surface.convert()
                    
                    _image_cache[cache_key] = surface
                    return surface
            
            except Exception as e:
                print(f"Error loading image {path}: {e}")
                return None
        
        assets_to_cache = []
        
        # Add player character based on stage
        if stage_number == 3:
            assets_to_cache.append(('Character', "assets/characters/subzero.png", (240, 333)))
        elif stage_number == 4:
            assets_to_cache.append(('Character', "assets/characters/atlantean_christie.png", (240, 333)))
        elif stage_number == 5:
            assets_to_cache.extend([
                ('Character', "assets/characters/subzero.png", (240, 333)),
                ('Character', "assets/characters/atlantean_kotal_kahn.png", (240, 333))
            ])
        elif stage_number == 6:
            assets_to_cache.extend([
                ('Character', "assets/characters/subzero.png", (240, 333)),
                ('Character', "assets/characters/atlantean_kotal_kahn.png", (240, 333)),
                ('Character', "assets/characters/atlantean_kagome.png", (240, 333))
            ])
        else:
            assets_to_cache.append(('Character', "assets/characters/atlantean_kagome.png", (240, 333)))
        
        # Add boss images based on stage
        if stage_number == 1:
            assets_to_cache.extend([
                ('Boss', "assets/characters/shadowfin.png", (240, 333)),
                ('Boss', "assets/characters/piranha.png", (240, 333))
            ])
        elif stage_number == 2:
            assets_to_cache.extend([
                ('Boss', "assets/characters/subzero_boss.png", (240, 333)),
                ('Boss', "assets/characters/ice_warrior.png", (240, 333))
            ])
        elif stage_number == 4:
            assets_to_cache.extend([
                ('Boss', "assets/characters/dark_leviathan.png", (240, 333))
            ])
        elif stage_number == 5:
            assets_to_cache.extend([
                ('Boss', "assets/characters/atlantean_zasalamel.png", (240, 333)),
                ('Boss', "assets/characters/shadow_assassin.png", (240, 333))
            ])
        
        # Add ability icons with proper identification
        ability_paths = [
            "assets/abilities/assassin_strike.png",
            "assets/abilities/shadowstep.png",
            "assets/abilities/water_bolt.png",
            "assets/abilities/tidal_wave.png",
            "assets/abilities/ice_lance.png",
            "assets/abilities/frost_armor.png",
            "assets/abilities/blizzard.png",
            "assets/abilities/ice_wall.png",
            "assets/abilities/kick.png",
            "assets/abilities/slam.png",
            # Add Stage 4 ability icons
            "assets/abilities/wave_crush.png",
            "assets/abilities/monstrous_scream.png",
            "assets/abilities/abyssal_regen.png",
            # Add Sub Zero's ability icons
            "assets/abilities/iceball.png",
            "assets/abilities/ice_clone.png",
            "assets/abilities/frozen_aura.png",
            "assets/abilities/summon_ice_warriors.png"
        ]
        for path in ability_paths:
            ability_name = os.path.splitext(os.path.basename(path))[0]
            assets_to_cache.append(('Ability Icon', path, (48, 48), ability_name))
        
        # Add item icons
        item_paths = [
            "assets/items/health_potion.png",
            "assets/items/mana_potion.png",
            "assets/items/piranha_scales.png",
            "assets/items/ice_shard.png",
            # Add Stage 4 item icons
            "assets/items/abyssal_echo.png",
            "assets/items/atlantean_trident_time.png",
            "assets/items/leviathan_scale.png",
            "assets/items/deep_sea_essence.png",
            "assets/items/murky_water_vial.png",
            "assets/items/leviathan_mist_vial.png"
        ]
        for path in item_paths:
            assets_to_cache.append(('Item Icon', path, (48, 48)))
        
        # Cache all assets with progress updates
        total_assets = len(assets_to_cache)
        for i, asset_info in enumerate(assets_to_cache):
            progress = (i + 1) / total_assets
            if len(asset_info) == 4:
                asset_type, path, size, asset_name = asset_info
                self.update_loading_progress(progress, f"Loading {asset_type}...")
                cache_image(path, size, asset_name)
            else:
                asset_type, path, size = asset_info
                self.update_loading_progress(progress, f"Loading {asset_type}...")
                cache_image(path, size)
    
    @staticmethod
    def get_cached_image(path: str, size: tuple = None, asset_name: str = None) -> Optional[pygame.Surface]:
        """Get an image from the cache if it exists."""
        cache_key = (path, size, asset_name) if asset_name else (path, size)
        return _image_cache.get(cache_key)
    
    @staticmethod
    def clear_image_cache():
        """Clear the global image cache."""
        _image_cache.clear()
    
    def show_modifier_selection(self):
        """Show the modifier selection window with random modifiers."""
        # First check if there are saved modifiers for the current stage
        has_saved_modifiers = False
        if hasattr(self, 'raid_inventory'):
            # Check modifiers for the current stage only
            saved_modifiers = self.raid_inventory.get_modifiers(
                "atlantean_raid",
                self.game_state.current_stage
            )
            has_saved_modifiers = bool(saved_modifiers)
        
        modifiers = self.modifier_manager.get_random_modifiers()
        self.modifier_selection.show(
            modifiers, 
            self.on_modifier_selected,
            self.on_continue_modifiers,
            self.on_restart_modifiers,
            self.on_reroll_modifiers,
            has_saved_modifiers
        )
        self.game_state.show_modifier_selection = True
    
    def on_modifier_selected(self, modifier):
        """Handle modifier selection."""
        self.modifier_manager.activate_modifier(modifier)
        self.game_state.show_modifier_selection = False
        
        # Apply battle start effects after modifier is selected
        self.modifier_manager.apply_battle_start(self)
        
        self.battle_log.add_message(
            f"Activated talent: {modifier.name}",
            self.battle_log.TEXT_COLOR
        )
        
    def on_continue_modifiers(self):
        """Handle continuing with saved modifiers."""
        print("\nContinuing with saved modifiers")
        # Load saved modifiers
        if self.modifier_manager.load_modifiers(self):
            self.game_state.show_modifier_selection = False
            # Apply battle start effects for all loaded modifiers
            print("Applying battle start effects for loaded modifiers")
            print(f"Active modifiers before battle start: {[m.name for m in self.modifier_manager.active_modifiers]}")
            self.modifier_manager.apply_battle_start(self)
            print(f"Active modifiers after battle start: {[m.name for m in self.modifier_manager.active_modifiers]}")
            
            # Update message based on stage
            if self.game_state.current_stage == 2:
                stage1_mods = self.raid_inventory.get_modifiers("atlantean_raid", 1)
                stage2_mods = self.raid_inventory.get_modifiers("atlantean_raid", 2)
                total_mods = len(stage1_mods) + len(stage2_mods)
                print(f"Stage 1 modifiers: {stage1_mods}")
                print(f"Stage 2 modifiers: {stage2_mods}")
                print(f"Total modifiers: {total_mods}")
                self.battle_log.add_message(
                    f"Continuing with {total_mods} saved talents from both stages",
                    self.battle_log.TEXT_COLOR
                )
            else:
                stage1_mods = self.raid_inventory.get_modifiers("atlantean_raid", 1)
                print(f"Stage 1 modifiers: {stage1_mods}")
                self.battle_log.add_message(
                    f"Continuing with {len(stage1_mods)} saved talents",
                    self.battle_log.TEXT_COLOR
                )
        else:
            # If load_modifiers returns False, show new modifier selection
            print("No modifiers found for current stage, showing selection")
            modifiers = self.modifier_manager.get_random_modifiers()
            self.modifier_selection.show(
                modifiers,
                self.on_modifier_selected,
                self.on_continue_modifiers,
                self.on_restart_modifiers,
                self.on_reroll_modifiers,
                False  # No saved modifiers
            )
    
    def on_restart_modifiers(self):
        """Handle restarting with new modifiers."""
        # Clear saved modifiers
        self.modifier_manager.clear_modifiers(self)
        # Clear active modifiers list
        self.modifier_manager.active_modifiers = []
        # Reset game state
        self.game_state.show_modifier_selection = True
        # Get new random modifiers
        modifiers = self.modifier_manager.get_random_modifiers()
        # Reset and show modifier selection window
        self.modifier_selection = ModifierSelectionWindow(self.screen_width, self.screen_height)
        self.modifier_selection.show(
            modifiers, 
            self.on_modifier_selected,
            self.on_continue_modifiers,
            self.on_restart_modifiers,
            self.on_reroll_modifiers,
            False  # Set has_saved_modifiers to False since we just cleared them
        )
        # Log the restart
        self.battle_log.add_message(
            "Restarting with new talents...",
            self.battle_log.TEXT_COLOR
        )
    
    def on_reroll_modifiers(self):
        """Handle rerolling modifiers."""
        # Get new random modifiers
        modifiers = self.modifier_manager.get_random_modifiers()
        # Show modifier selection window with new modifiers
        self.modifier_selection.show(
            modifiers, 
            self.on_modifier_selected,
            self.on_continue_modifiers,
            self.on_restart_modifiers,
            self.on_reroll_modifiers,
            False  # Set has_saved_modifiers to False since we're showing new modifiers
        )
        # Log the reroll
        self.battle_log.add_message(
            "Rerolling talents...",
            self.battle_log.TEXT_COLOR
        )
    
    def handle_ability_click(self, pos):
        if self.action_queue.is_busy:
            return
        if not self.game_state.is_player_turn:
            return
            
        char = self.stage_manager.player_characters[self.game_state.selected_character_index]
        for i, ability in enumerate(char.abilities):
            ability_rect = pygame.Rect(ability.position, (char.ABILITY_ICON_SIZE, char.ABILITY_ICON_SIZE))
            if ability_rect.collidepoint(pos):
                if ability.can_use(char):
                    self.game_state.selected_ability = i
                    # Execute immediately if it's an auto-target ability
                    if ability.auto_self_target:
                        self.execute_player_turn()
                return
        
        # Save game state after ability use
        # self.save_game_state()
    
    def handle_target_click(self, pos):
        """Handle clicking on a target when an ability or item is selected"""
        if self.action_queue.is_busy:
            return
        if not self.game_state.is_player_turn:
            return
            
        if self.game_state.targeting_item:
            # Handle item targeting
            char = self.stage_manager.player_characters[self.game_state.selected_character_index]
            
            # Check for self-targeting
            char_rect = pygame.Rect(char.position, char.image.get_size())
            if char_rect.collidepoint(pos):
                if self.inventory.use_selected_item(char):
                    self.game_state.targeting_item = False
                    # Sync inventory after using item
                    self.sync_inventory()
                    # Only end turn if the item is meant to end turn
                    if self.inventory.selected_item and hasattr(self.inventory.selected_item, 'ends_turn') and self.inventory.selected_item.ends_turn:
                        self.end_player_turn()
                    return
            
            # Check for boss targeting
            if self.stage_manager.current_stage:
                from characters.shadowfin_boss import Piranha
                for i, boss in enumerate(self.stage_manager.current_stage.bosses):
                    if boss.is_alive() and not isinstance(boss, Piranha) and boss.is_targetable():  # Check targetable
                        boss_rect = pygame.Rect(boss.position, boss.image.get_size())
                        if boss_rect.collidepoint(pos):
                            if self.inventory.use_selected_item(boss):
                                self.game_state.targeting_item = False
                                # Sync inventory after using item
                                self.sync_inventory()
                                # Only end turn if the item is meant to end turn
                                if self.inventory.selected_item and hasattr(self.inventory.selected_item, 'ends_turn') and self.inventory.selected_item.ends_turn:
                                    self.end_player_turn()
                                return
            
            # If we got here, either the target was invalid or the item couldn't be used
            self.inventory.cancel_selection()
            self.game_state.targeting_item = False
            return
            
        # Handle ability targeting
        if self.game_state.selected_ability is None:
            return
            
        char = self.stage_manager.player_characters[self.game_state.selected_character_index]
        ability = char.abilities[self.game_state.selected_ability]
        
        # Skip if it's an auto-target ability
        if ability.auto_self_target or any(effect.type == "damage_all" for effect in ability.effects):
            return
            
        # Check for self-targeting
        if ability.can_self_target:
            char_rect = pygame.Rect(char.position, char.image.get_size())
            if char_rect.collidepoint(pos):
                self.game_state.selected_target = None  # None indicates self-target
                self.execute_player_turn()
                return
                
        # Check for boss targeting
        if self.stage_manager.current_stage:
            from characters.shadowfin_boss import Piranha
            for i, boss in enumerate(self.stage_manager.current_stage.bosses):
                if boss.is_alive() and not isinstance(boss, Piranha) and boss.is_targetable():  # Check targetable
                    boss_rect = pygame.Rect(boss.position, boss.image.get_size())
                    if boss_rect.collidepoint(pos):
                        self.game_state.selected_target = i
                        self.execute_player_turn()
                        return
        
        # If clicked outside any valid target, cancel ability selection
        self.game_state.selected_ability = None
        self.game_state.selected_target = None
    
    def log_ability_use(self, char: Character, ability: "Ability", targets: List[Character]):
        # Log the ability use
        self.battle_log.add_message(
            f"{char.name} uses {ability.name}!",
            self.battle_log.TEXT_COLOR
        )
        
        # Log the effects
        for effect in ability.effects:
            if effect.type == "damage":
                # Calculate actual damage after reductions
                damage_reduction = targets[0].get_damage_reduction()
                reduced_amount = effect.value * (1 - damage_reduction / 100)
                final_damage = max(1, int(reduced_amount - targets[0].stats.defense))
                self.battle_log.add_message(
                    f"  Deals {final_damage} damage to {targets[0].name}",
                    self.battle_log.DAMAGE_COLOR
                )
            elif effect.type == "damage_all":
                self.battle_log.add_message(
                    f"  Deals damage to all enemies",
                    self.battle_log.DAMAGE_COLOR
                )
                # Log individual damage
                for target in targets:
                    # Calculate actual damage after reductions
                    damage_reduction = target.get_damage_reduction()
                    reduced_amount = effect.value * (1 - damage_reduction / 100)
                    final_damage = max(1, int(reduced_amount - target.stats.defense))
                    self.battle_log.add_message(
                        f"    {target.name} takes {final_damage} damage",
                        self.battle_log.DAMAGE_COLOR
                    )
            elif effect.type == "heal":
                self.battle_log.add_message(
                    f"  Heals for {effect.value}",
                    self.battle_log.HEAL_COLOR
                )
            elif effect.type == "restore_mana_self":
                self.battle_log.add_message(
                    f"  Restores {effect.value} mana",
                    self.battle_log.MANA_COLOR
                )
            elif effect.type in ["buff", "debuff"]:
                self.battle_log.add_message(
                    f"  {'Buffs' if effect.type == 'buff' else 'Debuffs'} target by {effect.value} for {effect.duration} turns",
                    self.battle_log.BUFF_COLOR
                )
            elif effect.type == "damage_reduction":
                self.battle_log.add_message(
                    f"  Reduces damage taken by {effect.value}% for {effect.duration} turns",
                    self.battle_log.BUFF_COLOR
                )
            elif effect.type == "heal_over_time":
                self.battle_log.add_message(
                    f"  Heals {effect.value} HP per turn for {effect.duration} turns",
                    self.battle_log.HEAL_COLOR
                )
            elif effect.type == "remove_effects":
                for target in targets:
                    self.battle_log.add_message(
                        f"  Removes all buffs and debuffs from {target.name}",
                        self.battle_log.BUFF_COLOR
                    )
    
    def end_player_turn(self):
        char = self.stage_manager.player_characters[self.game_state.selected_character_index]
        self.game_state.is_player_turn = False
        self.game_state.selected_ability = None
        self.game_state.selected_target = None
        self.game_state.turn_count += 1
        
        # Update item cooldowns
        if char.inventory:
            for item in char.inventory.slots:
                if item and item.current_cooldown > 0:
                    item.current_cooldown -= 1
        
        # Update cooldowns for all characters at end of full turn
        for char in self.stage_manager.player_characters:
            char.end_turn()
            # Update player ability cooldowns
            for ability in char.abilities:
                if ability.current_cooldown > 0:
                    ability.current_cooldown -= 1
            # Update item cooldowns
            if char.inventory:
                for item in char.inventory.slots:
                    if item and item.current_cooldown > 0:
                        item.current_cooldown -= 1
        
        # Update boss cooldowns and effects
        if self.stage_manager.current_stage:
            for boss in self.stage_manager.current_stage.bosses:
                boss.end_turn()
                for ability in boss.abilities:
                    if ability.current_cooldown > 0:
                        ability.current_cooldown -= 1
        
        # Apply modifier effects
        self.modifier_manager.apply_turn_end(self)
        
        # Notify stage of turn end
        if self.stage_manager.current_stage:
            self.stage_manager.current_stage.on_turn_end()
        
        # Apply modifier effects at turn start
        self.modifier_manager.apply_turn_start(self)
        
        # Sync inventory after modifiers are applied
        self.sync_inventory()
        
        # Log turn end
        self.battle_log.add_message(
            f"Turn {self.game_state.turn_count} begins!",
            self.battle_log.TEXT_COLOR
        )
    
    def execute_player_turn(self):
        if (self.game_state.selected_ability is None or 
            not self.stage_manager.current_stage):
            return
            
        char = self.stage_manager.player_characters[self.game_state.selected_character_index]
        ability = char.abilities[self.game_state.selected_ability]
        
        # For AoE abilities, target all bosses
        if any(effect.type == "damage_all" for effect in ability.effects):
            from characters.shadowfin_boss import Piranha
            targets = [boss for boss in self.stage_manager.current_stage.bosses if boss.is_alive() and not isinstance(boss, Piranha)]
        # For auto-self-target abilities, target self
        elif ability.auto_self_target:
            targets = [char]
        # For single target abilities, need a target selected
        elif self.game_state.selected_target is None:
            return
        else:
            targets = [self.stage_manager.current_stage.bosses[self.game_state.selected_target]]
        
        if ability.use(char, targets):
            self.log_ability_use(char, ability, targets)
            self.end_player_turn()
        
        # Save game state after each turn
        # self.save_game_state()
    
    def execute_boss_turn(self):
        if not self.stage_manager.current_stage:
            return
        
        bosses = self.stage_manager.current_stage.bosses
        if not hasattr(self, '_current_boss_index'):
            self._current_boss_index = 0
        
        if self._current_boss_index < len(bosses):
            boss = bosses[self._current_boss_index]
            if boss.is_alive():
                from characters.shadowfin_boss import create_shadowfin_boss, Piranha
                # For other bosses, use random abilities
                available_abilities = [i for i, ability in enumerate(boss.abilities) if ability.is_available()]
                if available_abilities:
                    ability_idx = np.random.choice(available_abilities)
                    ability = boss.abilities[ability_idx]
                    
                    # Special handling for Shadowfin's Call Piranha ability
                    if boss.name == "Shadowfin" and ability == boss.abilities[-1]:
                        def ability_action():
                            if ability.use(boss, [boss]):
                                self.battle_log.add_message(
                                    f"{boss.name} uses {ability.name}!",
                                    self.battle_log.TEXT_COLOR
                                )
                        self.action_queue.add_action(ability_action, duration=0.0)
                    else:
                        # For all other abilities, target players
                        valid_targets = [char for char in self.stage_manager.player_characters if char.is_alive()]
                        if valid_targets:  # Only proceed if there are valid targets
                            target = np.random.choice(valid_targets)
                            
                            def ability_action():
                                if ability.use(boss, [target]):
                                    # Log the boss ability use
                                    self.battle_log.add_message(
                                        f"{boss.name} uses {ability.name}!",
                                        self.battle_log.TEXT_COLOR
                                    )
                                    
                                    # Log the effects
                                    for effect in ability.effects:
                                        if effect.type == "damage":
                                            # Calculate actual damage after reductions
                                            damage_reduction = target.get_damage_reduction()
                                            reduced_amount = effect.value * (1 - damage_reduction / 100)
                                            final_damage = max(1, int(reduced_amount - target.stats.defense))
                                            self.battle_log.add_message(
                                                f"  Deals {final_damage} damage to {target.name}",
                                                self.battle_log.DAMAGE_COLOR
                                            )
                                        elif effect.type == "heal":
                                            self.battle_log.add_message(
                                                f"  Heals for {effect.value}",
                                                self.battle_log.HEAL_COLOR
                                            )
                                        elif effect.type == "restore_mana_self":
                                            self.battle_log.add_message(
                                                f"  Restores {effect.value} mana",
                                                self.battle_log.MANA_COLOR
                                            )
                                        elif effect.type in ["buff", "debuff"]:
                                            self.battle_log.add_message(
                                                f"  {'Buffs' if effect.type == 'buff' else 'Debuffs'} target by {effect.value} for {effect.duration} turns",
                                                self.battle_log.BUFF_COLOR
                                            )
                            self.action_queue.add_action(ability_action, duration=0.0)
                
                # Move to next boss immediately after queueing the action
                self._current_boss_index += 1
        else:
            self._current_boss_index = 0
            self.game_state.is_player_turn = True
    
    def handle_target_hover(self, pos):
        """Handle mouse hover over potential targets"""
        self.hovered_target = None
        
        if not self.game_state.is_player_turn:
            return
            
        if self.game_state.targeting_item:
            # Handle item targeting hover
            char = self.stage_manager.player_characters[self.game_state.selected_character_index]
            char_rect = pygame.Rect(char.position, char.image.get_size())
            if char_rect.collidepoint(pos):
                self.hovered_target = ("player", 0)
                return
            
            if self.stage_manager.current_stage:
                from characters.shadowfin_boss import Piranha
                for i, boss in enumerate(self.stage_manager.current_stage.bosses):
                    if boss.is_alive() and not isinstance(boss, Piranha) and boss.is_targetable():  # Check targetable
                        boss_rect = pygame.Rect(boss.position, boss.image.get_size())
                        if boss_rect.collidepoint(pos):
                            self.hovered_target = ("boss", i)
                            return
            return
            
        if self.game_state.selected_ability is None:
            return
            
        char = self.stage_manager.player_characters[self.game_state.selected_character_index]
        ability = char.abilities[self.game_state.selected_ability]
        
        # Skip if it's an auto-target ability
        if ability.auto_self_target or any(effect.type == "damage_all" for effect in ability.effects):
            return
        
        # Check for self-targeting
        if ability.can_self_target:
            char_rect = pygame.Rect(char.position, char.image.get_size())
            if char_rect.collidepoint(pos):
                self.hovered_target = ("player", 0)
                return
        
        # Check for boss targeting
        if self.stage_manager.current_stage:
            from characters.shadowfin_boss import Piranha
            for i, boss in enumerate(self.stage_manager.current_stage.bosses):
                if boss.is_alive() and not isinstance(boss, Piranha) and boss.is_targetable():  # Check targetable
                    boss_rect = pygame.Rect(boss.position, boss.image.get_size())
                    if boss_rect.collidepoint(pos):
                        self.hovered_target = ("boss", i)
                        return
    
    def draw_target_indicators(self):
        """Draw indicators for valid targets"""
        if not self.game_state.is_player_turn:
            return
            
        if self.game_state.targeting_item:
            # Draw target indicators for item use
            char = self.stage_manager.player_characters[self.game_state.selected_character_index]
            
            # Draw self-target indicator
            char_rect = pygame.Rect(char.position, char.image.get_size())
            is_hovered = self.hovered_target and self.hovered_target[0] == "player"
            color = self.HOVERED_TARGET_COLOR if is_hovered else self.VALID_TARGET_COLOR
            self.draw_target_indicator(char_rect, color)
            
            # Draw boss target indicators
            if self.stage_manager.current_stage:
                from characters.shadowfin_boss import Piranha
                for i, boss in enumerate(self.stage_manager.current_stage.bosses):
                    if boss.is_alive() and not isinstance(boss, Piranha):  # Filter out piranhas
                        boss_rect = pygame.Rect(boss.position, boss.image.get_size())
                        is_hovered = self.hovered_target and self.hovered_target[0] == "boss" and self.hovered_target[1] == i
                        color = self.HOVERED_TARGET_COLOR if is_hovered else self.VALID_TARGET_COLOR
                        self.draw_target_indicator(boss_rect, color)
            return
            
        if self.game_state.selected_ability is None:
            return
            
        char = self.stage_manager.player_characters[self.game_state.selected_character_index]
        ability = char.abilities[self.game_state.selected_ability]
        
        # Skip if it's an auto-target ability
        if ability.auto_self_target or any(effect.type == "damage_all" for effect in ability.effects):
            return
        
        # Draw self-target indicator if applicable
        if ability.can_self_target:
            char_rect = pygame.Rect(char.position, char.image.get_size())
            is_hovered = self.hovered_target and self.hovered_target[0] == "player"
            color = self.HOVERED_TARGET_COLOR if is_hovered else self.VALID_TARGET_COLOR
            self.draw_target_indicator(char_rect, color)
        
        # Draw boss target indicators
        if self.stage_manager.current_stage:
            from characters.shadowfin_boss import Piranha
            for i, boss in enumerate(self.stage_manager.current_stage.bosses):
                if boss.is_alive() and not isinstance(boss, Piranha):  # Filter out piranhas
                    boss_rect = pygame.Rect(boss.position, boss.image.get_size())
                    is_hovered = self.hovered_target and self.hovered_target[0] == "boss" and self.hovered_target[1] == i
                    color = self.HOVERED_TARGET_COLOR if is_hovered else self.VALID_TARGET_COLOR
                    self.draw_target_indicator(boss_rect, color)
    
    def draw_target_indicator(self, target_rect: pygame.Rect, color: tuple):
        """Draw a target indicator with given color"""
        # Calculate pulsing alpha based on time
        pulse = (math.sin(self.game_state.target_highlight_time * 5) + 1) / 2  # Value between 0 and 1
        alpha = int(100 + pulse * 100)  # Pulsing between 100 and 200 alpha
        
        # Create larger rect for the indicator
        indicator_rect = target_rect.inflate(20, 20)
        
        # Create surface for the indicator
        indicator_surface = pygame.Surface(indicator_rect.size, pygame.SRCALPHA)
        
        # Draw the indicator with pulsing alpha
        color_with_alpha = (*color[:3], alpha)
        pygame.draw.rect(indicator_surface, color_with_alpha, indicator_surface.get_rect(), 
                        width=3, border_radius=10)
        
        # Add corner markers
        marker_size = 15
        marker_color = (*color[:3], alpha + 50)  # Slightly more opaque
        
        # Top-left corner
        pygame.draw.line(indicator_surface, marker_color, (0, marker_size), (0, 0), 3)
        pygame.draw.line(indicator_surface, marker_color, (0, 0), (marker_size, 0), 3)
        
        # Top-right corner
        pygame.draw.line(indicator_surface, marker_color, (indicator_rect.width - marker_size, 0), (indicator_rect.width, 0), 3)
        pygame.draw.line(indicator_surface, marker_color, (indicator_rect.width, 0), (indicator_rect.width, marker_size), 3)
        
        # Bottom-left corner
        pygame.draw.line(indicator_surface, marker_color, (0, indicator_rect.height - marker_size), (0, indicator_rect.height), 3)
        pygame.draw.line(indicator_surface, marker_color, (0, indicator_rect.height), (marker_size, indicator_rect.height), 3)
        
        # Bottom-right corner
        pygame.draw.line(indicator_surface, marker_color, (indicator_rect.width - marker_size, indicator_rect.height), (indicator_rect.width, indicator_rect.height), 3)
        pygame.draw.line(indicator_surface, marker_color, (indicator_rect.width, indicator_rect.height - marker_size), (indicator_rect.width, indicator_rect.height), 3)
        
        # Draw glow effect
        glow_surface = pygame.Surface(indicator_rect.size, pygame.SRCALPHA)
        glow_color = (*color[:3], int(alpha * 0.3))  # More transparent for glow
        pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect(), 
                        border_radius=10)
        
        # Draw the glow and indicator
        self.screen.blit(glow_surface, indicator_rect)
        self.screen.blit(indicator_surface, indicator_rect)
    
    def handle_single_event(self, event: pygame.event.Event):
        """Handle a single event."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Handle loot window first
                if self.loot_window:
                    kept_items = self.loot_window.handle_event(event)
                    if kept_items is not None:
                        # Add kept items to inventory
                        for item in kept_items:
                            self.raid_inventory.add_item(item.name, item.stack_count)
                        
                        # Refresh from database to ensure we have the latest state
                        self.raid_inventory.load_inventory()
                        
                        # Save to database
                        self.raid_inventory.save_inventory()
                        
                        # Clear both inventories
                        for char in self.stage_manager.player_characters:
                            if char.inventory:
                                char.inventory.slots = [None] * 6
                        self.inventory.slots = [None] * 6
                        
                        # Repopulate both inventories from RaidInventory
                        for char in self.stage_manager.player_characters:
                            if char.inventory:
                                self.raid_inventory.populate_ui_inventory(char.inventory)
                        self.raid_inventory.populate_ui_inventory(self.inventory)
                        
                        self.pending_loot = []  # Clear pending loot
                        self.loot_window = None  # Close loot window
                        return
                
                # Handle character selection first
                for i, char in enumerate(self.stage_manager.player_characters):
                    if char.is_alive():
                        char_rect = pygame.Rect(char.position, char.image.get_size())
                        if char_rect.collidepoint(event.pos):
                            # Only select character if not targeting
                            if not self.game_state.targeting_item and self.game_state.selected_ability is None:
                                self.game_state.selected_character_index = i
                                # Log character selection
                                self.battle_log.add_message(
                                    f"Selected {char.name}",
                                    self.battle_log.TEXT_COLOR
                                )
                                return
                
                # Handle end turn button first
                if self.game_state.is_player_turn and self.stage_manager.handle_events(event):
                    self.end_player_turn()
                    return
                
                # Then handle ability and target selection
                if not self.game_state.targeting_item and self.game_state.selected_ability is None:
                    self.handle_ability_click(event.pos)
                else:
                    self.handle_target_click(event.pos)
        elif event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            if self.game_state.targeting_item:
                # Cancel item targeting
                self.inventory.cancel_selection()
                self.game_state.targeting_item = False
            else:
                self.running = False
        elif event.type == pygame.MOUSEMOTION:
            # Handle ability tooltips
            for char in self.stage_manager.player_characters:
                for ability in char.abilities:
                    ability.handle_mouse_motion(event.pos)
            if self.stage_manager.current_stage:
                for boss in self.stage_manager.current_stage.bosses:
                    for ability in boss.abilities:
                        ability.handle_mouse_motion(event.pos)
            # Handle target hover
            self.handle_target_hover(event.pos)
        elif event.type == pygame.KEYDOWN:
            # Check for debug console toggle (Ctrl+0)
            if event.key == pygame.K_0 and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.debug_console.toggle()
                return
                
            if self.game_state.is_player_turn:
                if event.key == pygame.K_ESCAPE and self.game_state.targeting_item:
                    # Cancel item targeting
                    self.inventory.cancel_selection()
                    self.game_state.targeting_item = False
                    return
                
                # Handle ability hotkeys
                ability_index = None
                if event.key == pygame.K_q:
                    ability_index = 0
                elif event.key == pygame.K_w:
                    ability_index = 1
                elif event.key == pygame.K_e:
                    ability_index = 2
                elif event.key == pygame.K_r:
                    ability_index = 3
                
                # Handle character selection hotkeys (1-4)
                char_index = None
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                    char_index = event.key - pygame.K_1  # Convert key to 0-based index
                    if char_index < len(self.stage_manager.player_characters):
                        char = self.stage_manager.player_characters[char_index]
                        if char.is_alive():
                            self.game_state.selected_character_index = char_index
                            # Log character selection
                            self.battle_log.add_message(
                                f"Selected {char.name}",
                                self.battle_log.TEXT_COLOR
                            )
                            return
                
                if ability_index is not None:
                    char = self.stage_manager.player_characters[self.game_state.selected_character_index]
                    if ability_index < len(char.abilities):
                        ability = char.abilities[ability_index]
                        if ability.can_use(char):
                            self.game_state.selected_ability = ability_index
                            # Execute immediately if it's an auto-target ability
                            if ability.auto_self_target:
                                self.execute_player_turn()
            elif event.type == pygame.MOUSEMOTION:
                # Handle ability tooltips
                for char in self.stage_manager.player_characters:
                    for ability in char.abilities:
                        ability.handle_mouse_motion(event.pos)
                if self.stage_manager.current_stage:
                    for boss in self.stage_manager.current_stage.bosses:
                        for ability in boss.abilities:
                            ability.handle_mouse_motion(event.pos)
                # Handle target hover
                self.handle_target_hover(event.pos)
    
    def handle_events(self):
        """Handle all pending pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # Handle debug console events first when it's visible
            if self.debug_console.visible:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # Close debug console when ESC is pressed
                    self.debug_console.visible = False
                    continue
                if self.debug_console.handle_event(event):
                    continue
            
            # Handle stage selector events
            if self.stage_selector.visible:
                if self.stage_selector.handle_event(event):
                    continue
            
            # Handle modifier selection events
            elif self.game_state.show_modifier_selection:
                if self.modifier_selection.handle_event(event):
                    continue
            
            # Handle game events
            else:
                # Handle inventory events first
                if self.inventory and self.inventory.handle_event(event):
                    continue
                
                # Handle battle log events
                if self.battle_log and self.battle_log.handle_event(event):
                    continue
                
                # Handle loot window events
                if self.loot_window:
                    kept_items = self.loot_window.handle_event(event)
                    if kept_items is not None:
                        # Add kept items to inventory
                        for item in kept_items:
                            self.raid_inventory.add_item(item.name, item.stack_count)
                        
                        # Refresh from database to ensure we have the latest state
                        self.raid_inventory.load_inventory()
                        
                        # Save to database
                        self.raid_inventory.save_inventory()
                        
                        # Clear both inventories
                        for char in self.stage_manager.player_characters:
                            if char.inventory:
                                char.inventory.slots = [None] * 6
                        self.inventory.slots = [None] * 6
                        
                        # Repopulate both inventories from RaidInventory
                        for char in self.stage_manager.player_characters:
                            if char.inventory:
                                self.raid_inventory.populate_ui_inventory(char.inventory)
                        self.raid_inventory.populate_ui_inventory(self.inventory)
                        
                        self.pending_loot = []  # Clear pending loot
                        self.loot_window = None  # Close loot window
                        continue
                
                # Handle stage manager events
                if self.game_state.is_player_turn and self.stage_manager.handle_events(event):
                    self.end_player_turn()
                    continue
                
                # Handle single game event
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.game_state.targeting_item:
                        # Cancel item targeting
                        self.inventory.cancel_selection()
                        self.game_state.targeting_item = False
                    else:
                        # Only close game if not targeting item and debug console is not visible
                        self.running = False
                else:
                    self.handle_single_event(event)
    
    def draw_target_highlight(self, target_rect: pygame.Rect):
        # Calculate pulsing alpha based on time
        pulse = (math.sin(self.game_state.target_highlight_time * 5) + 1) / 2  # Value between 0 and 1
        alpha = int(100 + pulse * 50)  # Pulsing between 100 and 150 alpha
        
        # Create highlight surface
        highlight_rect = target_rect.inflate(20, 20)  # Make highlight slightly larger than target
        highlight_surface = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
        
        # Draw outer glow
        glow_color = (*self.TARGET_HIGHLIGHT_COLOR[:3], alpha)
        pygame.draw.rect(highlight_surface, glow_color, highlight_surface.get_rect(), 
                        border_radius=10)
        
        # Draw border
        border_color = (*self.TARGET_HIGHLIGHT_COLOR[:3], alpha + 50)
        pygame.draw.rect(highlight_surface, border_color, highlight_surface.get_rect(), 
                        width=3, border_radius=10)
        
        # Draw the highlight
        self.screen.blit(highlight_surface, highlight_rect)
    
    def update(self):
        """Update game state."""
        # Update action queue first
        self.action_queue.update()
        
        # Only proceed with other updates if no actions are in progress
        if not self.action_queue.is_busy:
            # Update debug console
            self.debug_console.update()
            
            # Only update game if modifier selection is not showing
            if not self.game_state.show_modifier_selection:
                self.stage_manager.update()
                
                # Update target highlight time
                self.game_state.target_highlight_time += self.clock.get_time() / 1000.0  # Convert to seconds
                
                # Update visual effects
                dt = self.clock.get_time() / 1000.0  # Convert to seconds
                self.visual_effects.update(dt)
                
                # Update character abilities
                for char in self.stage_manager.player_characters:
                    for ability in char.abilities:
                        ability.update()
                
                if self.stage_manager.current_stage:
                    for boss in self.stage_manager.current_stage.bosses:
                        for ability in boss.abilities:
                            ability.update()
                
                if self.stage_manager.is_battle_won():
                    # Just log the victory
                    self.battle_log.add_message("Victory! The boss has been defeated!", self.battle_log.TEXT_COLOR)
                elif self.stage_manager.is_battle_lost():
                    # Just log the defeat
                    self.battle_log.add_message("Defeat! Your party has fallen...", self.battle_log.TEXT_COLOR)
                elif not self.game_state.is_player_turn:
                    self.execute_boss_turn()
            
            # Update stage selector animations
            self.stage_selector.update()
        
        pygame.display.flip()
    
    def sync_inventory(self):
        """Helper method to sync UI inventory with RaidInventory."""
        for char in self.stage_manager.player_characters:
            if char.inventory:
                char.inventory.slots = [None] * 6
                self.raid_inventory.populate_ui_inventory(char.inventory)
    
    def draw_turn_counter(self):
        # Turn counter container
        padding = 20
        margin = 20
        text = f"Turn {self.game_state.turn_count}"
        text_surface = self.turn_font.render(text, True, self.TURN_TEXT_COLOR)
        text_width = text_surface.get_width() + padding * 2
        text_height = text_surface.get_height() + padding
        
        # Default wave text surface for non-Stage 4 stages
        wave_text_surface = pygame.font.Font(None, 24).render("", True, (0, 150, 255))

    def render(self):
        """Render the game state to the screen."""
        # Clear screen
        self.screen.fill(self.BG_COLOR)
        
        # Draw stage selector if visible
        if self.stage_selector.visible:
            self.stage_selector.draw(self.screen)
            pygame.display.flip()
            return
        
        if self.game_state.show_modifier_selection:
            # Only draw the modifier selection window
            self.modifier_selection.draw(self.screen)
        else:
            # Draw the rest of the game
            # Draw stage background
            if self.stage_manager.current_stage:
                self.stage_manager.current_stage.draw(self.screen)
            
            # Draw characters
            for char in self.stage_manager.player_characters:
                char.draw(self.screen)
            
            if self.stage_manager.current_stage:
                for boss in self.stage_manager.current_stage.bosses:
                    boss.draw(self.screen)
            
            # Draw target indicators for valid targets
            self.draw_target_indicators()
            
            # Draw visual effects
            self.visual_effects.draw(self.screen)
            
            # Draw end turn button
            self.stage_manager.draw(self.screen)
            
            # Draw turn counter
            self.draw_turn_counter()
            
            # Highlight selected ability
            if self.game_state.selected_ability is not None:
                char = self.stage_manager.player_characters[self.game_state.selected_character_index]
                ability = char.abilities[self.game_state.selected_ability]
                pygame.draw.rect(self.screen, (255, 255, 0), 
                               (*ability.position, char.ABILITY_ICON_SIZE, char.ABILITY_ICON_SIZE), 2)
            
            # Draw battle log
            self.battle_log.draw(self.screen)
            
            # Draw inventory
            self.inventory.draw(self.screen)
            
            # Draw ability tooltips
            for char in self.stage_manager.player_characters:
                for ability in char.abilities:
                    ability.draw_tooltip(self.screen)
            if self.stage_manager.current_stage:
                for boss in self.stage_manager.current_stage.bosses:
                    for ability in boss.abilities:
                        ability.draw_tooltip(self.screen)
            
            # Draw loot window if there are pending drops
            if self.pending_loot:
                self.loot_window.draw(self.screen)
            
            # Draw debug console last (on top)
            self.debug_console.draw(self.screen)
            
            # Draw active modifiers in top-right corner
            self.active_modifiers_display.draw(self.screen, self.modifier_manager.active_modifiers)
        
        pygame.display.flip()

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()  # This now handles all events
            self.update()
            self.render()
            self.clock.tick(60)
        
        pygame.quit()

    def handle_character_death(self, character: Character):
        """Handle a character's death, including loot drops and character removal."""
        # Only process loot if it hasn't been processed yet
        if not hasattr(character, 'loot_processed') or not character.loot_processed:
            # Get the character's loot table from the current stage
            if self.stage_manager and self.stage_manager.current_stage:
                loot_table = self.stage_manager.current_stage.get_loot_table(type(character))
                if loot_table:
                    # Roll for loot
                    dropped_items = loot_table.roll_loot()
                    if dropped_items:
                        # Create loot window if there are items
                        window_x = (self.screen_width - 500) // 2  # Center horizontally
                        window_y = (self.screen_height - 800) // 2  # Center vertically
                        self.loot_window = LootWindow(window_x, window_y)
                        self.loot_window.set_items(dropped_items)
                        
                        # Store pending loot
                        self.pending_loot = dropped_items
            
            # Mark loot as processed
            character.loot_processed = True
        
        # Remove character from appropriate lists
        if character in self.stage_manager.player_characters:
            self.stage_manager.player_characters.remove(character)
        if self.stage_manager.current_stage and character in self.stage_manager.current_stage.bosses:
            self.stage_manager.current_stage.bosses.remove(character)

if __name__ == "__main__":
    game = GameEngine()
    game.run() 