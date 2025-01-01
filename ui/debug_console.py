import pygame
from typing import Dict, Callable, List
from items.consumables import (
    MurkyWaterVial, PiranhaTooth, DeepSeaEssence, IceShard, IceFlask, 
    IceDagger, LeviathanMistVial, AbyssalEcho, ManaPotion, AtlanteanTrident,
    UnderwaterCursedShell, CursedWaterVial
)
from items.buffs import PiranhaScales, TidalCharm, VoidEssence, ShadowDagger
from items.legendary_items import IceBlade, ZasalamelsScythe

class DebugConsole:
    # Colors
    BG_COLOR = (0, 0, 0, 200)  # Semi-transparent black
    TEXT_COLOR = (0, 255, 0)  # Matrix green
    CURSOR_COLOR = (0, 255, 0)
    
    def __init__(self, width: int, height: int = 200):
        self.rect = pygame.Rect(0, 0, width, height)
        self.visible = False
        self.font = pygame.font.Font(None, 24)
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Text input state
        self.input_text = ""
        self.cursor_visible = True
        self.cursor_blink_time = 0
        
        # Command history
        self.command_history: List[str] = []
        self.history_index = 0
        
        # Register commands
        self.commands: Dict[str, Callable] = {
            "items": self.handle_items_command,
            "enemy": self.handle_enemy_command,
            "help": self.show_help,
            "clear": self.clear_console,
            "piranha": self.handle_piranha_command,
            "item": self.handle_single_item_command,
            "turn": self.handle_turn_command,
            "cooldown": self.handle_cooldown_command
        }
        
        # Console output
        self.output_lines: List[str] = []
        self.max_lines = 8
    
    def handle_items_command(self, args: List[str]) -> bool:
        """Handle item-related commands."""
        if len(args) < 2:
            return False
        
        if args[0] == "test" and args[1] == "add":
            # Add test items to inventory
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                # Create and add test items
                items = [
                    MurkyWaterVial(),  # Common healing item
                    DeepSeaEssence(),  # Rare mana and cooldown item
                    TidalCharm(),      # Common healing boost item
                    VoidEssence()      # Rare damage boost item
                ]
                
                for item in items:
                    GameEngine.instance.inventory.add_item(item)
                
                self.add_output("Added test items to inventory")
                return True
        
        return False
    
    def handle_enemy_command(self, args: List[str]) -> bool:
        """Handle enemy-related commands."""
        if len(args) < 2:
            return False
        
        if args[0] == "test" and args[1] == "hp":
            # Set all enemy HP to 5
            from engine.game_engine import GameEngine
            if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
                stage = GameEngine.instance.stage_manager.current_stage
                for enemy in stage.bosses:
                    enemy.stats.current_hp = 5
                    enemy.stats.current_hp = min(enemy.stats.current_hp, enemy.stats.max_hp)
                
                self.add_output("Set all enemy HP to 5")
                return True
        
        return False
    
    def handle_piranha_command(self, args: List[str]) -> bool:
        """Handle piranha spawn command."""
        if len(args) < 2 or not args[0] == "test" or not args[1].isdigit():
            self.add_output("Usage: piranha test <number>")
            return False
        
        # Get number of piranhas to spawn
        num_piranhas = int(args[1])
        
        from engine.game_engine import GameEngine
        from characters.shadowfin_boss import Piranha
        from items.loot_table import LootTable
        from items.consumables import MurkyWaterVial, PiranhaTooth
        from items.buffs import PiranhaScales
        
        if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
            stage = GameEngine.instance.stage_manager.current_stage
            
            # Set up loot table for piranhas if not already set
            if not stage.get_loot_table(Piranha):
                piranha_loot = LootTable(min_total_drops=0, max_total_drops=3)  # 0-3 items total
                piranha_loot.add_entry(PiranhaTooth, 10.0, 0, 1)    # 10% chance for Piranha Tooth
                piranha_loot.add_entry(PiranhaScales, 30.0, 0, 1)   # 30% chance for Piranha Scales
                piranha_loot.add_entry(MurkyWaterVial, 60.0, 0, 1)  # 60% chance for Murky Water Vial
                stage.add_loot_table(Piranha, piranha_loot)
            
            # Create and add piranhas
            for _ in range(num_piranhas):
                piranha = Piranha()
                stage.bosses.append(piranha)
            
            self.add_output(f"Spawned {num_piranhas} piranhas")
            return True
        
        return False
    
    def handle_single_item_command(self, args: List[str]) -> bool:
        """Handle single item command: item test <itemname>"""
        if len(args) < 2 or args[0] != "test":
            return False
            
        item_name = args[1].lower()
        
        # Import GameEngine locally to avoid circular import
        import sys
        if 'engine.game_engine' in sys.modules:
            game_instance = sys.modules['engine.game_engine'].GameEngine.instance
        else:
            self.add_output("Error: Game engine not initialized")
            return True
        
        if not game_instance or not game_instance.stage_manager.player_characters:
            self.add_output("Error: No active game or player characters")
            return True
            
        item_map = {
            "murky": MurkyWaterVial,
            "piranha": PiranhaTooth,
            "essence": DeepSeaEssence,
            "iceshard": IceShard,
            "iceflask": IceFlask,
            "icedagger": IceDagger,
            "mistvial": LeviathanMistVial,
            "abyssalecho": AbyssalEcho,
            "manapotion": ManaPotion,
            "trident": AtlanteanTrident,
            "attm": AtlanteanTrident,  # Alternative shorter name
            "zs": ZasalamelsScythe,    # Zasalamel's Scythe
            "scythe": ZasalamelsScythe, # Alternative name
            "shell": UnderwaterCursedShell,  # Underwater Cursed Shell
            "cursedshell": UnderwaterCursedShell,  # Alternative name
            "cursedvial": CursedWaterVial,  # Cursed Water Vial
            "cursedwater": CursedWaterVial  # Alternative name
        }
        
        if item_name in item_map:
            item_class = item_map[item_name]
            item = item_class()
            game_instance.inventory.add_item(item)
            self.add_output(f"Added {item_name} to inventory")
            return True
        
        return False
    
    def handle_turn_command(self, args: List[str]) -> bool:
        """Handle turn test command."""
        if len(args) < 2 or not args[0] == "test" or not args[1].isdigit():
            self.add_output("Usage: turn test <number>")
            return False
        
        from engine.game_engine import GameEngine
        if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
            stage = GameEngine.instance.stage_manager.current_stage
            if hasattr(stage, 'handle_debug_command'):
                command = f"turn test {args[1]}"
                if stage.handle_debug_command(command):
                    self.add_output(f"Set turn counter to {args[1]}")
                    return True
        
        return False
    
    def handle_cooldown_command(self, args: List[str]) -> bool:
        """Handle cooldown test command."""
        if len(args) < 2 or not args[0] == "test" or not args[1].isdigit():
            self.add_output("Usage: cooldown test <number>")
            return False
        
        cooldown = int(args[1])
        
        from engine.game_engine import GameEngine
        if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
            # Set cooldowns for player characters
            for char in GameEngine.instance.stage_manager.player_characters:
                for ability in char.abilities:
                    ability.current_cooldown = cooldown
            
            # Set cooldowns for boss characters
            for boss in GameEngine.instance.stage_manager.current_stage.bosses:
                for ability in boss.abilities:
                    ability.current_cooldown = cooldown
            
            self.add_output(f"Set all ability cooldowns to {cooldown}")
            return True
        
        return False
    
    def show_help(self, args: List[str]) -> None:
        """Show available commands and their usage."""
        self.add_output("Available commands:")
        self.add_output("  items test add - Add test items to inventory")
        self.add_output("  enemy test hp - Set all enemy HP to 5")
        self.add_output("  piranha test <number> - Spawn specified number of piranhas")
        self.add_output("  item test iceblade - Add Ice Blade to inventory")
        self.add_output("  item test iceshard - Add Ice Shard to inventory")
        self.add_output("  item test iceflask - Add Ice Flask to inventory")
        self.add_output("  item test icedagger - Add Ice Dagger to inventory")
        self.add_output("  item test shadowdagger - Add Shadow Dagger to inventory")
        self.add_output("  turn test <number> - Set turn counter to specified number")
        self.add_output("  cooldown test <number> - Set all ability cooldowns to specified number")
        self.add_output("  help - Show this help message")
        self.add_output("  clear - Clear the console")
    
    def clear_console(self, args: List[str]) -> None:
        """Clear the console output."""
        self.output_lines.clear()
        self.add_output("Console cleared")
    
    def add_output(self, text: str) -> None:
        """Add a line of text to the console output."""
        self.output_lines.append(text)
        if len(self.output_lines) > self.max_lines:
            self.output_lines.pop(0)
    
    def toggle(self) -> None:
        """Toggle console visibility."""
        self.visible = not self.visible
        if self.visible:
            self.input_text = ""
            self.cursor_visible = True
            self.cursor_blink_time = pygame.time.get_ticks()
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle keyboard events for the console."""
        if not self.visible:
            return
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Execute command
                if self.input_text:
                    self.execute_command(self.input_text)
                    self.command_history.append(self.input_text)
                    self.history_index = len(self.command_history)
                    self.input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.toggle()
            elif event.key == pygame.K_UP:
                # Navigate command history
                if self.command_history and self.history_index > 0:
                    self.history_index -= 1
                    self.input_text = self.command_history[self.history_index]
            elif event.key == pygame.K_DOWN:
                # Navigate command history
                if self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.input_text = self.command_history[self.history_index]
                elif self.history_index == len(self.command_history) - 1:
                    self.history_index = len(self.command_history)
                    self.input_text = ""
            else:
                # Add character to input
                if event.unicode.isprintable():
                    self.input_text += event.unicode
    
    def execute_command(self, command: str) -> None:
        """Execute a console command."""
        self.add_output(f"> {command}")
        parts = command.lower().split()
        if not parts:
            return
            
        cmd = parts[0]
        args = parts[1:]
        
        if cmd in self.commands:
            self.commands[cmd](args)
        else:
            self.add_output(f"Unknown command: {cmd}")
            self.add_output("Type 'help' for available commands")
    
    def update(self) -> None:
        """Update console state."""
        if not self.visible:
            return
            
        # Update cursor blink
        current_time = pygame.time.get_ticks()
        if current_time - self.cursor_blink_time > 500:  # Blink every 500ms
            self.cursor_visible = not self.cursor_visible
            self.cursor_blink_time = current_time
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the console."""
        if not self.visible:
            return
            
        # Clear surface
        self.surface.fill(self.BG_COLOR)
        
        # Draw output lines
        y = 10
        for line in self.output_lines:
            text_surface = self.font.render(line, True, self.TEXT_COLOR)
            self.surface.blit(text_surface, (10, y))
            y += self.font.get_height()
        
        # Draw input line with cursor
        input_prefix = "> "
        prefix_surface = self.font.render(input_prefix, True, self.TEXT_COLOR)
        self.surface.blit(prefix_surface, (10, self.rect.height - 30))
        
        input_surface = self.font.render(self.input_text, True, self.TEXT_COLOR)
        self.surface.blit(input_surface, (30, self.rect.height - 30))
        
        # Draw cursor
        if self.cursor_visible:
            cursor_x = 30 + input_surface.get_width()
            pygame.draw.line(
                self.surface,
                self.CURSOR_COLOR,
                (cursor_x, self.rect.height - 30),
                (cursor_x, self.rect.height - 10),
                2
            )
        
        # Draw to screen
        screen.blit(self.surface, self.rect) 