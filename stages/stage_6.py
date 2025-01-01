from stages.base_stage import BaseStage
from characters.base_character import Character, Stats
from characters.subzero import create_subzero
from characters.atlantean_kotal_kahn import create_atlantean_kotal_kahn
from characters.atlantean_kagome import create_atlantean_kagome
from characters.atlantean_shinnok import create_atlantean_shinnok
from typing import List
import pygame
import types
import random
from modifiers.modifier_manager import ModifierManager
from modifiers.modifier_base import Modifier
from stages.stage_3 import create_ice_warrior

class DarkBubblePrison:
    def __init__(self):
        self.type = "debuff"
        self.name = "Dark Bubble Prison"
        self.description = "Character is trapped in a dark bubble, disabling all abilities for 2 turns"
        self.duration = 2  # 2 turns duration
        self.icon = pygame.image.load("assets/buffs/dark_bubble.png")
        self.is_removable = False  # Cannot be removed until duration expires
        self.affected_character = None
        print("[DarkBubblePrison] Created new instance")
        
    def get_tooltip_title(self):
        return self.name
        
    def get_tooltip_text(self):
        return f"{self.description}\nDuration: {self.duration} turns"
        
    def update(self):
        if self.duration > 0:
            self.duration -= 1
            print(f"[DarkBubblePrison] Duration reduced to {self.duration}")
            if self.duration == 0:
                print("[DarkBubblePrison] Duration expired, cleaning up...")
                self.on_remove()  # Call on_remove to properly restore abilities
            return True
        return False

    def apply_x_overlay(self, ability):
        """Apply X overlay to ability icon"""
        print(f"[DarkBubblePrison] Applying X overlay to ability: {ability.name}")
        
        # Store original icon
        ability._original_icon = ability.icon.copy()
        
        # Create X overlay
        x_size = ability.icon.get_width()
        x_surface = pygame.Surface((x_size, x_size), pygame.SRCALPHA)
        x_color = (255, 0, 0, 180)  # Semi-transparent red
        x_thickness = 4  # Thicker lines for better visibility
        
        # Draw black outline for better visibility
        outline_color = (0, 0, 0, 180)
        outline_thickness = x_thickness + 2
        pygame.draw.line(x_surface, outline_color, (0, 0), (x_size, x_size), outline_thickness)
        pygame.draw.line(x_surface, outline_color, (0, x_size), (x_size, 0), outline_thickness)
        
        # Draw red X
        pygame.draw.line(x_surface, x_color, (0, 0), (x_size, x_size), x_thickness)
        pygame.draw.line(x_surface, x_color, (0, x_size), (x_size, 0), x_thickness)
        
        # Combine X with the original icon
        combined_surface = ability._original_icon.copy()
        combined_surface.blit(x_surface, (0, 0))
        ability.icon = combined_surface
        
        # Create and bind the draw method with cooldown and mana handling
        def draw_with_x(self_ability, screen):
            # Draw the icon (which now includes the X)
            screen.blit(self_ability.icon, self_ability.position)
            
            # Draw cooldown overlay if not available
            if not self_ability.is_available():
                cooldown_surface = pygame.Surface(self_ability.icon.get_size(), pygame.SRCALPHA)
                cooldown_surface.fill((0, 0, 0, 128))  # Semi-transparent black
                screen.blit(cooldown_surface, self_ability.position)
                
                # Draw cooldown number
                font = pygame.font.Font(None, 36)
                text = font.render(str(self_ability.current_cooldown), True, (255, 255, 255))
                text_rect = text.get_rect(center=(self_ability.position[0] + 25, self_ability.position[1] + 25))
                screen.blit(text, text_rect)
            
            # Draw mana cost
            if self_ability.mana_cost > 0:
                font = pygame.font.Font(None, 24)
                mana_text = str(self_ability.mana_cost)
                text_surface = font.render(mana_text, True, (64, 156, 255))  # Blue color for mana
                text_rect = text_surface.get_rect(bottomright=(self_ability.position[0] + self_ability.icon.get_width() - 2,
                                                             self_ability.position[1] + self_ability.icon.get_height() - 2))
                
                # Draw text shadow
                shadow_surface = font.render(mana_text, True, (0, 0, 0))
                shadow_rect = text_rect.copy()
                shadow_rect.x += 1
                shadow_rect.y += 1
                screen.blit(shadow_surface, shadow_rect)
                screen.blit(text_surface, text_rect)
        
        # Store original draw method and bind new one
        ability._original_draw = ability.draw if hasattr(ability, 'draw') else None
        ability.draw = types.MethodType(draw_with_x, ability)

    def on_apply(self, target: Character):
        """Called when the debuff is applied"""
        print(f"[DarkBubblePrison] Applying debuff to {target.name}")
        self.affected_character = target
        
        # Disable all abilities
        for ability in target.abilities:
            print(f"[DarkBubblePrison] Disabling ability: {ability.name}")
            ability.is_disabled = True
            self.apply_x_overlay(ability)

    def on_remove(self):
        """Called when the debuff is removed"""
        if self.affected_character:
            print(f"[DarkBubblePrison] Removing debuff from {self.affected_character.name}")
            for ability in self.affected_character.abilities:
                print(f"[DarkBubblePrison] Re-enabling ability: {ability.name}")
                ability.is_disabled = False
                # Restore original icon
                if hasattr(ability, '_original_icon'):
                    ability.icon = ability._original_icon

class AtlanteanShinnok(Character):
    """Atlantean Shinnok boss class"""
    def __init__(self):
        stats = Stats(
            max_hp=12000,
            current_hp=12000,
            max_mana=1000,
            current_mana=1000,
            attack=100,
            defense=20,
            speed=6
        )
        super().__init__("Atlantean Shinnok", stats, "assets/characters/atlantean_shinnok.png")

class AtlanteanKagome(Character):
    """Atlantean Kagome character class"""
    def __init__(self):
        stats = Stats(
            max_hp=6500,
            current_hp=6500,
            max_mana=2000,
            current_mana=2000,
            attack=75,
            defense=15,
            speed=7
        )
        super().__init__("Atlantean Kagome", stats, "assets/characters/kagome.png")

class Stage6(BaseStage):
    """Final stage - Battle against Atlantean Shinnok"""
    def __init__(self):
        super().__init__(
            name="The Final Battle",
            description="Face off against the mighty Atlantean Shinnok in an epic final battle. Your chosen heroes must work together to defeat this powerful adversary.",
            background_path="assets/backgrounds/stage6.png",
            stage_number=6
        )
        self.game_started = False
        self.boss = None
        self.difficulty = 5.0  # Maximum difficulty
        self.dark_bubble_active = False
        self.current_bubble_target = None
        
        # Initialize modifier manager
        self.modifier_manager = ModifierManager()
        
    def setup_bosses(self) -> List[Character]:
        """Set up the boss for this stage"""
        self.boss = create_atlantean_shinnok()
        
        # Add anti-summoning curse buff
        class AntiSummoningCurse:
            def __init__(self):
                self.type = "custom"
                self.name = "Anti-Summoning Curse"
                self.description = "Disables any companion or summons"
                self.duration = float('inf')  # Permanent buff
                self.icon = pygame.image.load("assets/buffs/anti_summon_magic.png")
                self.is_removable = False  # Cannot be removed
                
            def get_tooltip_title(self):
                return self.name
                
            def get_tooltip_text(self):
                return self.description
                
            def update(self):
                return True  # Never expires
        
        self.boss.buffs.append(AntiSummoningCurse())
        return [self.boss]
        
    def on_enter(self):
        """Called when entering the stage"""
        # Create player characters
        subzero = create_subzero()
        kotal_kahn = create_atlantean_kotal_kahn()
        kagome = create_atlantean_kagome()
        
        # Add ice warriors ability to SubZero first
        from abilities.base_ability import Ability, AbilityEffect
        summon_warriors = Ability(
            name="Call Ice Warriors",
            description="Call forth frozen warriors to aid in battle.",
            icon_path="assets/abilities/summon_ice_warriors.png",
            effects=[],  # Special handling in use method
            cooldown=10,
            mana_cost=80,
            auto_self_target=True  # Auto target self for W/ability2
        )
        
        # Create X overlay on the icon
        x_size = 48  # Standard ability icon size
        x_surface = pygame.Surface((x_size, x_size), pygame.SRCALPHA)
        x_color = (255, 0, 0, 180)  # Semi-transparent red
        x_thickness = 4  # Thicker lines for better visibility
        
        # Draw black outline for better visibility
        outline_color = (0, 0, 0, 180)
        outline_thickness = x_thickness + 2
        pygame.draw.line(x_surface, outline_color, (0, 0), (x_size, x_size), outline_thickness)
        pygame.draw.line(x_surface, outline_color, (0, x_size), (x_size, 0), outline_thickness)
        
        # Draw red X
        pygame.draw.line(x_surface, x_color, (0, 0), (x_size, x_size), x_thickness)
        pygame.draw.line(x_surface, x_color, (0, x_size), (x_size, 0), x_thickness)
        
        # Combine the X with the original icon
        if summon_warriors.icon:
            combined_surface = summon_warriors.icon.copy()
            combined_surface.blit(x_surface, (0, 0))
            summon_warriors.icon = combined_surface
        
        # Make ability unclickable by setting cooldown to infinity
        summon_warriors.cooldown = float('inf')
        summon_warriors.current_cooldown = float('inf')
        
        # Add disabled ability to Sub Zero
        subzero.add_ability(summon_warriors)
        
        # Disable ice warriors ability for this stage
        def disabled_ice_warriors(*args, **kwargs):
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    "Ice Warriors cannot be summoned in the final battle!",
                    GameEngine.instance.battle_log.TEXT_COLOR
                )
            return False
            
        # Create and bind the draw method with X overlay
        def draw_with_x(ability, screen):
            # Draw the original icon
            screen.blit(ability.icon, ability.position)
            
            # Create a new surface for the X overlay
            x_size = ability.icon.get_width()
            x_surface = pygame.Surface((x_size, x_size), pygame.SRCALPHA)
            x_color = (255, 0, 0, 180)  # Semi-transparent red
            x_thickness = 4  # Thicker lines for better visibility
            
            # Draw black outline for better visibility
            outline_color = (0, 0, 0, 180)
            outline_thickness = x_thickness + 2
            pygame.draw.line(x_surface, outline_color, (0, 0), (x_size, x_size), outline_thickness)
            pygame.draw.line(x_surface, outline_color, (0, x_size), (x_size, 0), outline_thickness)
            
            # Draw red X
            pygame.draw.line(x_surface, x_color, (0, 0), (x_size, x_size), x_thickness)
            pygame.draw.line(x_surface, x_color, (0, x_size), (x_size, 0), x_thickness)
            
            # Draw the X overlay
            screen.blit(x_surface, ability.position)
            
            # Draw cooldown overlay if not available
            if not ability.is_available():
                cooldown_surface = pygame.Surface(ability.icon.get_size(), pygame.SRCALPHA)
                cooldown_surface.fill((0, 0, 0, 128))  # Semi-transparent black
                screen.blit(cooldown_surface, ability.position)
                
                # Draw cooldown number
                font = pygame.font.Font(None, 36)
                text = font.render(str(ability.current_cooldown), True, (255, 255, 255))
                text_rect = text.get_rect(center=(ability.position[0] + 25, ability.position[1] + 25))
                screen.blit(text, text_rect)
            
            # Draw mana cost
            if ability.mana_cost > 0:
                font = pygame.font.Font(None, 24)
                mana_text = str(ability.mana_cost)
                text_surface = font.render(mana_text, True, (64, 156, 255))  # Blue color for mana
                text_rect = text_surface.get_rect(bottomright=(ability.position[0] + ability.icon.get_width() - 2,
                                                             ability.position[1] + ability.icon.get_height() - 2))
                
                # Draw text shadow
                shadow_surface = font.render(mana_text, True, (0, 0, 0))
                shadow_rect = text_rect.copy()
                shadow_rect.x += 1
                shadow_rect.y += 1
                screen.blit(shadow_surface, shadow_rect)
                screen.blit(text_surface, text_rect)
        
        summon_warriors.use = disabled_ice_warriors
        summon_warriors.draw = types.MethodType(draw_with_x, summon_warriors)
        
        # Set up player characters
        from engine.game_engine import GameEngine
        GameEngine.instance.stage_manager.player_characters = [
            subzero,
            kotal_kahn,
            kagome
        ]
        
        # Load modifiers from all stages
        if GameEngine.instance and hasattr(GameEngine.instance, 'modifier_manager'):
            # Load modifiers from all stages
            for stage_num in range(1, 6):  # Load stages 1 through 5
                stage_modifiers = GameEngine.instance.raid_inventory.get_modifiers("atlantean_raid", stage_num)
                
                # Load modifiers
                for modifier_name in stage_modifiers:
                    if modifier_name in GameEngine.instance.modifier_manager.modifier_map:
                        modifier = GameEngine.instance.modifier_manager.modifier_map[modifier_name]()
                        modifier.activate()
                        GameEngine.instance.modifier_manager.active_modifiers.append(modifier)
            
            # Apply battle start effects for all loaded modifiers
            GameEngine.instance.modifier_manager.apply_battle_start(GameEngine.instance)
        
        # Position characters
        self.update_character_positions()
        
        self.game_started = True
        
        # Handle Fishnet modifier if active
        if GameEngine.instance and hasattr(GameEngine.instance, 'modifier_manager'):
            for modifier in GameEngine.instance.modifier_manager.active_modifiers:
                if modifier.__class__.__name__ == "Fishnet":
                    # Create X overlay for modifier icon
                    if hasattr(modifier, 'image_path') and modifier.image_path:
                        icon = pygame.image.load(modifier.image_path)
                        x_size = icon.get_width()
                        x_surface = pygame.Surface((x_size, x_size), pygame.SRCALPHA)
                        x_color = (255, 0, 0, 180)  # Semi-transparent red
                        x_thickness = 4  # Thicker lines for better visibility
                        
                        # Draw black outline for better visibility
                        outline_color = (0, 0, 0, 180)
                        outline_thickness = x_thickness + 2
                        pygame.draw.line(x_surface, outline_color, (0, 0), (x_size, x_size), outline_thickness)
                        pygame.draw.line(x_surface, outline_color, (0, x_size), (x_size, 0), outline_thickness)
                        
                        # Draw red X
                        pygame.draw.line(x_surface, x_color, (0, 0), (x_size, x_size), x_thickness)
                        pygame.draw.line(x_surface, x_color, (0, x_size), (x_size, 0), x_thickness)
                        
                        # Combine X with the original icon
                        icon.blit(x_surface, (0, 0))
                        # Update the modifier's icon
                        modifier.icon = icon
                    
                    # Disable the modifier
                    modifier.is_active = False
                    # Remove any existing Piranha
                    from characters.shadowfin_boss import Piranha
                    GameEngine.instance.stage_manager.player_characters = [
                        char for char in GameEngine.instance.stage_manager.player_characters 
                        if not isinstance(char, Piranha)
                    ]
                    # Add message to battle log
                    GameEngine.instance.battle_log.add_message(
                        "__Shinnok's anti-summoning curse prevents the Piranha from being summoned!__",
                        (255, 0, 0)  # Red color
                    )
                    break
        
    def apply_modifier(self, modifier: Modifier):
        """Apply a modifier to the stage"""
        from engine.game_engine import GameEngine
        if modifier.affects_player:
            for character in GameEngine.instance.stage_manager.player_characters:
                modifier.apply(character)
                
        if modifier.affects_boss:
            modifier.apply(self.boss)
        
    def update_character_positions(self):
        """Update positions of all characters"""
        if not hasattr(self, '_screen_dimensions'):
            self._screen_dimensions = (1920, 1080)
            
        # Position Shinnok in the center
        if self.boss:
            center_x = self._screen_dimensions[0] // 2
            self.boss.position = (center_x - self.boss.image.get_width() // 2, 50)
        
        # Position player characters
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            alive_players = [p for p in GameEngine.instance.stage_manager.player_characters if p.is_alive()]
            if alive_players:
                player_spacing = self._screen_dimensions[0] // (len(alive_players) + 1)
                for i, player in enumerate(alive_players, 1):
                    x = player_spacing * i - player.image.get_width() // 2
                    player.position = (x, 600)
    
    def update(self):
        """Update stage state"""
        super().update()
        self.update_character_positions()
        
    def draw(self, screen: pygame.Surface):
        """Draw the stage"""
        # Draw background
        super().draw(screen)
        
        # Update character positions
        self.update_character_positions()
        
        # Draw boss
        if self.boss:
            self.boss.draw(screen)
        
        # Draw player characters
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            alive_players = [p for p in GameEngine.instance.stage_manager.player_characters if p.is_alive()]
            for player in alive_players:
                player.draw(screen)

    def on_turn_end(self):
        """Called at the end of each turn"""
        from engine.game_engine import GameEngine
        
        # Update character positions
        self.update_character_positions()
        
        # Update modifiers
        if GameEngine.instance and hasattr(GameEngine.instance, 'modifier_manager'):
            GameEngine.instance.modifier_manager.apply_turn_end(GameEngine.instance)
            
        # Update boss abilities cooldowns
        if self.boss:
            for ability in self.boss.abilities:
                if ability.current_cooldown > 0:
                    ability.current_cooldown -= 1
        
        # Handle Dark Bubble Prison mechanic
        player_characters = GameEngine.instance.stage_manager.player_characters
        
        if not self.dark_bubble_active:
            # Initialize Dark Bubble Prison on a random character
            target = random.choice(player_characters)
            self.apply_dark_bubble_prison(target)
        else:
            # Check if current bubble needs to be transferred
            current_bubbles = [debuff for debuff in self.current_bubble_target.debuffs 
                           if isinstance(debuff, DarkBubblePrison)]
            
            if not current_bubbles:
                # Previous bubble expired, apply to new random target
                available_targets = [char for char in player_characters 
                                  if char != self.current_bubble_target]
                if available_targets:
                    new_target = random.choice(available_targets)
                    self.apply_dark_bubble_prison(new_target)
    
    def apply_dark_bubble_prison(self, target: Character):
        """Apply Dark Bubble Prison to a target character"""
        print(f"[Stage6] Applying Dark Bubble Prison to {target.name}")
        
        # Create the Dark Bubble Prison debuff
        bubble = DarkBubblePrison()
        
        # Debug print current debuffs
        print(f"[Stage6] Current debuffs for {target.name}:")
        for debuff in target.debuffs:
            print(f"[Stage6] - {debuff.name}")
        
        # Apply the debuff effects
        bubble.on_apply(target)
        
        # Add to debuffs
        target.debuffs.append(bubble)
        print(f"[Stage6] Added Dark Bubble Prison to {target.name}'s debuffs")
        
        # Debug print abilities after applying debuff
        print(f"[Stage6] Abilities after applying Dark Bubble Prison:")
        for ability in target.abilities:
            print(f"[Stage6] - {ability.name} (disabled: {ability.is_disabled})")
        
        self.dark_bubble_active = True
        self.current_bubble_target = target
        
        # Add message to battle log
        from engine.game_engine import GameEngine
        GameEngine.instance.battle_log.add_message(
            f"__Dark Bubble Prison ensnares {target.name}!__",
            (128, 0, 128)  # Purple color
        ) 