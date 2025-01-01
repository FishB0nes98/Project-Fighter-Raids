from dataclasses import dataclass
from typing import List, Optional, Callable, TYPE_CHECKING
import pygame
from pathlib import Path
import random
from PIL import Image
import os

if TYPE_CHECKING:
    from characters.base_character import Character

@dataclass
class AbilityEffect:
    type: str  # "damage", "heal", "buff", "debuff", "damage_reduction", "heal_over_time", "increase_cooldowns"
    value: int
    duration: Optional[int] = None  # For buffs/debuffs
    chance: Optional[float] = None  # For effects with probability

class Ability:
    # Colors
    TOOLTIP_BG_COLOR = (32, 36, 44, 240)  # Dark background with slight transparency
    TOOLTIP_BORDER_COLOR = (64, 68, 76)
    TOOLTIP_INNER_BORDER_COLOR = (80, 84, 92)
    TOOLTIP_TEXT_COLOR = (220, 220, 220)
    TOOLTIP_TITLE_COLOR = (255, 255, 255)  # Pure white for title
    TOOLTIP_MANA_COLOR = (64, 156, 255)
    TOOLTIP_DAMAGE_COLOR = (255, 96, 96)
    TOOLTIP_HEAL_COLOR = (96, 255, 96)
    TOOLTIP_SHADOW_COLOR = (0, 0, 0, 60)  # Semi-transparent black for shadows
    
    def __init__(self, 
                 name: str,
                 description: str,
                 icon_path: str,
                 effects: List[AbilityEffect],
                 cooldown: int = 0,
                 mana_cost: int = 0,
                 auto_self_target: bool = False,
                 can_self_target: bool = True):
        self.name = name
        self.description = description
        self.effects = effects
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.mana_cost = mana_cost
        self.auto_self_target = auto_self_target
        self.can_self_target = can_self_target
        self.is_hovered = False
        self.is_disabled = False
        
        # Get the ability icon from cache or load it
        from engine.game_engine import GameEngine
        ability_name = os.path.splitext(os.path.basename(icon_path))[0]
        self.icon = GameEngine.get_cached_image(icon_path, (50, 50), ability_name)
        
        # If not in cache, load it directly
        if self.icon is None:
            # Load ability icon with high quality scaling
            pil_image = Image.open(str(Path(icon_path)))
            pil_image = pil_image.convert('RGBA')  # Ensure RGBA mode for transparency
            pil_image = pil_image.resize((50, 50), Image.Resampling.LANCZOS)  # High quality resize
            
            # Convert PIL image to Pygame surface
            image_data = pil_image.tobytes()
            self.icon = pygame.image.fromstring(image_data, pil_image.size, 'RGBA')
            self.icon = self.icon.convert_alpha()  # Convert for faster blitting
        
        self.position = (0, 0)  # Will be set by the game engine
        
        # Tooltip fonts with better sizes
        self.tooltip_font = pygame.font.Font(None, 26)  # Slightly larger for better readability
        self.tooltip_title_font = pygame.font.Font(None, 32)  # Larger title
        self.tooltip_detail_font = pygame.font.Font(None, 24)  # Smaller for details
    
    def handle_mouse_motion(self, mouse_pos: tuple[int, int]):
        ability_rect = pygame.Rect(self.position, self.icon.get_size())
        self.is_hovered = ability_rect.collidepoint(mouse_pos)
    
    def draw_tooltip(self, screen: pygame.Surface):
        if not self.is_hovered:
            return
            
        padding = 16  # Increased padding
        line_spacing = 6  # Increased line spacing
        max_width = 300  # Maximum width for text wrapping
        
        # Prepare text surfaces with shadows
        title_shadow = self.tooltip_title_font.render(self.name, True, (0, 0, 0))
        title_surface = self.tooltip_title_font.render(self.name, True, self.TOOLTIP_TITLE_COLOR)
        
        # Split description into wrapped lines
        desc_words = self.description.split()
        desc_lines = []
        current_line = []
        
        for word in desc_words:
            test_line = ' '.join(current_line + [word])
            test_surface = self.tooltip_font.render(test_line, True, self.TOOLTIP_TEXT_COLOR)
            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    desc_lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    desc_lines.append(word)
        if current_line:
            desc_lines.append(' '.join(current_line))
        
        desc_surfaces = [self.tooltip_font.render(line, True, self.TOOLTIP_TEXT_COLOR) 
                        for line in desc_lines]
        
        # Create effect text lines
        effect_lines = []
        for effect in self.effects:
            text = ""  # Initialize text for each effect
            color = self.TOOLTIP_TEXT_COLOR  # Default color
            
            if effect.type == "damage":
                text = f"Deals {effect.value} damage"
                color = self.TOOLTIP_DAMAGE_COLOR
            elif effect.type == "heal":
                text = f"Heals for {effect.value} HP"
                color = self.TOOLTIP_HEAL_COLOR
            elif effect.type == "remove_effects":
                text = "Removes all buffs and debuffs"
            elif effect.type in ["buff", "debuff"]:
                text = f"{'Buffs' if effect.type == 'buff' else 'Debuffs'} target by {effect.value} for {effect.duration} turns"
            elif effect.type == "increase_cooldowns":
                if hasattr(effect, 'chance'):
                    text = f"Has a {int(effect.chance * 100)}% chance to increase all enemy ability cooldowns by {effect.value} turn{'s' if effect.value > 1 else ''}"
                else:
                    text = f"Increases all enemy ability cooldowns by {effect.value} turn{'s' if effect.value > 1 else ''}"
            elif effect.type == "damage_reduction":
                text = f"Reduces damage taken by {effect.value}% for {effect.duration} turns"
            elif effect.type == "heal_over_time":
                text = f"Heals for {effect.value} HP over {effect.duration} turns"
            else:
                text = f"{effect.type.replace('_', ' ').title()}: {effect.value}"
            
            effect_lines.append((text, color))
        
        # Create effect surfaces
        effect_surfaces = [(self.tooltip_font.render(text, True, color), color) 
                          for text, color in effect_lines]
        
        # Calculate tooltip dimensions
        width = max(
            title_surface.get_width(),
            *[surface.get_width() for surface in desc_surfaces],
            *[surface.get_width() for surface, _ in effect_surfaces]
        ) + padding * 3  # Extra padding for modern look
        
        height = (padding * 2 + title_surface.get_height() + line_spacing +
                 sum(surface.get_height() + line_spacing for surface in desc_surfaces) +
                 line_spacing * 2 +  # Extra spacing after description
                 sum(surface.get_height() + line_spacing for surface, _ in effect_surfaces))
        
        # Add space for mana cost and cooldown
        if self.mana_cost > 0 or self.cooldown > 0:
            height += line_spacing + self.tooltip_detail_font.get_height()
        
        # Position tooltip to the right of the ability icon
        x = self.position[0] + self.icon.get_width() + 10
        y = self.position[1]
        
        # Keep tooltip on screen
        if x + width > screen.get_width():
            x = self.position[0] - width - 10
        if y + height > screen.get_height():
            y = screen.get_height() - height
        
        # Draw tooltip shadow
        shadow_rect = pygame.Rect(x + 4, y + 4, width, height)
        pygame.draw.rect(screen, self.TOOLTIP_SHADOW_COLOR, shadow_rect, border_radius=10)
        
        # Draw main tooltip background
        tooltip_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, self.TOOLTIP_BG_COLOR, tooltip_rect, border_radius=10)
        
        # Draw border with gradient effect
        border_rect = tooltip_rect.inflate(2, 2)
        pygame.draw.rect(screen, self.TOOLTIP_BORDER_COLOR, border_rect, width=2, border_radius=10)
        inner_border = tooltip_rect.inflate(-2, -2)
        pygame.draw.rect(screen, self.TOOLTIP_INNER_BORDER_COLOR, inner_border, width=1, border_radius=9)
        
        current_y = y + padding
        
        # Draw title with shadow
        screen.blit(title_shadow, (x + padding + 1, current_y + 1))
        screen.blit(title_surface, (x + padding, current_y))
        current_y += title_surface.get_height() + line_spacing
        
        # Draw separator line
        separator_y = current_y - line_spacing//2
        pygame.draw.line(screen, self.TOOLTIP_INNER_BORDER_COLOR,
                        (x + padding, separator_y),
                        (x + width - padding, separator_y))
        
        # Draw description lines
        for desc_surface in desc_surfaces:
            screen.blit(desc_surface, (x + padding, current_y))
            current_y += desc_surface.get_height() + line_spacing
        
        current_y += line_spacing  # Extra spacing after description
        
        # Draw effects
        for i, (effect_surface, color) in enumerate(effect_surfaces):
            # Draw shadow
            text = effect_lines[i][0]  # Get the original text
            shadow = self.tooltip_font.render(text, True, (0, 0, 0))
            screen.blit(shadow, (x + padding + 1, current_y + 1))
            screen.blit(effect_surface, (x + padding, current_y))
            current_y += effect_surface.get_height() + line_spacing
        
        # Draw mana cost and cooldown with icons
        if self.mana_cost > 0 or self.cooldown > 0:
            current_y += line_spacing  # Extra space before stats
            pygame.draw.line(screen, self.TOOLTIP_INNER_BORDER_COLOR,
                           (x + padding, current_y - line_spacing//2),
                           (x + width - padding, current_y - line_spacing//2))
            
            if self.mana_cost > 0:
                mana_text = f"Mana Cost: {self.mana_cost}"
                mana_surface = self.tooltip_detail_font.render(mana_text, True, self.TOOLTIP_MANA_COLOR)
                screen.blit(mana_surface, (x + padding, current_y))
            
            if self.cooldown > 0:
                cooldown_text = f"Cooldown: {self.cooldown} turns"
                cooldown_surface = self.tooltip_detail_font.render(cooldown_text, True, self.TOOLTIP_TEXT_COLOR)
                if self.mana_cost > 0:
                    screen.blit(cooldown_surface, (x + width//2, current_y))
                else:
                    screen.blit(cooldown_surface, (x + padding, current_y))
    
    def is_available(self) -> bool:
        return self.current_cooldown == 0
    
    def can_use(self, caster: "Character") -> bool:
        """Check if the ability can be used (cooldown and mana)"""
        # Check if ability is disabled
        if self.is_disabled:
            return False
            
        # Check if caster is under Spiritwalk effect
        for buff in caster.buffs:
            if buff.type == "damage_reduction" and not hasattr(buff, 'is_protection'):
                return False  # Cannot use abilities while under Spiritwalk
            
            # Check for mana cost modifiers
            if hasattr(buff, 'modify_mana_cost'):
                modified_cost = buff.modify_mana_cost(self.mana_cost)
                return self.is_available() and caster.stats.current_mana >= modified_cost
        
        return self.is_available() and caster.stats.current_mana >= self.mana_cost
    
    def use(self, caster: "Character", targets: List["Character"]) -> bool:
        """Use the ability on the target(s)"""
        if not self.can_use(caster):
            return False
            
        # Apply effects
        for effect in self.effects:
            # Check if effect has chance and if it should be applied
            if effect.chance is not None and random.random() > effect.chance:
                continue
                
            if effect.type == "damage":
                for target in targets:
                    damage = effect.value
                    # Apply damage reduction
                    damage_reduction = target.get_damage_reduction()
                    reduced_damage = damage * (1 - damage_reduction / 100)
                    final_damage = max(1, int(reduced_damage - target.stats.defense))
                    target.take_damage(final_damage)
                    
            elif effect.type == "increase_cooldowns":
                # Get all enemies from the game engine
                from engine.game_engine import GameEngine
                if GameEngine.instance:
                    current_stage = GameEngine.instance.stage_manager.current_stage
                    if current_stage:
                        # Determine if this is a player or boss ability to target the correct group
                        if isinstance(current_stage.bosses[0], type(GameEngine.instance.stage_manager.player_characters[0])):
                            enemies = GameEngine.instance.stage_manager.player_characters
                        else:
                            enemies = current_stage.bosses
                            
                        # Increase cooldowns for all abilities of all enemies
                        for enemy in enemies:
                            for ability in enemy.abilities:
                                if ability.current_cooldown > 0:
                                    ability.current_cooldown += effect.value
                                else:
                                    ability.current_cooldown = effect.value
                                    
            # Handle other effect types...
            elif effect.type == "heal":
                for target in targets:
                    target.heal(effect.value)
            # ... rest of the effect handling ...
            
        # Consume mana and set cooldown
        caster.stats.current_mana -= self.mana_cost
        self.current_cooldown = self.cooldown
        return True
    
    def update(self):
        """Update ability state. Cooldowns are handled by the game engine."""
        pass
    
    def draw(self, screen: pygame.Surface):
        screen.blit(self.icon, self.position)
        
        # Draw X indicator when ability is disabled
        if self.is_disabled:
            # Create a semi-transparent dark overlay
            overlay = pygame.Surface(self.icon.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))  # Semi-transparent black background
            screen.blit(overlay, self.position)
            
            # Draw red X with white outline for better visibility
            x_color = (255, 0, 0)  # Red color for the X
            outline_color = (255, 255, 255)  # White outline
            x_thickness = 4  # Increased thickness
            icon_size = self.icon.get_size()
            padding = 8  # Increased padding for larger X
            
            # Helper function to draw a line with outline
            def draw_outlined_line(start_pos, end_pos):
                # Draw white outline
                pygame.draw.line(screen, outline_color, start_pos, end_pos, x_thickness + 2)
                # Draw red center
                pygame.draw.line(screen, x_color, start_pos, end_pos, x_thickness)
            
            # Draw the X lines with outline
            start_pos1 = (self.position[0] + padding, self.position[1] + padding)
            end_pos1 = (self.position[0] + icon_size[0] - padding, self.position[1] + icon_size[1] - padding)
            start_pos2 = (self.position[0] + padding, self.position[1] + icon_size[1] - padding)
            end_pos2 = (self.position[0] + icon_size[0] - padding, self.position[1] + padding)
            
            draw_outlined_line(start_pos1, end_pos1)
            draw_outlined_line(start_pos2, end_pos2)
        
        # Draw cooldown overlay if not available
        if not self.is_available():
            cooldown_surface = pygame.Surface(self.icon.get_size(), pygame.SRCALPHA)
            cooldown_surface.fill((0, 0, 0, 128))  # Semi-transparent black
            screen.blit(cooldown_surface, self.position)
            
            # Draw cooldown number
            font = pygame.font.Font(None, 36)
            text = font.render(str(self.current_cooldown), True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.position[0] + 25, self.position[1] + 25))
            screen.blit(text, text_rect)
        
        # Draw mana cost
        if self.mana_cost > 0:
            font = pygame.font.Font(None, 24)
            mana_text = str(self.mana_cost)
            text_surface = font.render(mana_text, True, (64, 156, 255))  # Blue color for mana
            text_rect = text_surface.get_rect(bottomright=(self.position[0] + self.icon.get_width() - 2,
                                                         self.position[1] + self.icon.get_height() - 2))
            
            # Draw text shadow
            shadow_surface = font.render(mana_text, True, (0, 0, 0))
            shadow_rect = text_rect.copy()
            shadow_rect.x += 1
            shadow_rect.y += 1
            screen.blit(shadow_surface, shadow_rect)
            screen.blit(text_surface, text_rect)
        
        # Draw tooltip if hovered
        self.draw_tooltip(screen)

@dataclass
class StatusEffect:
    def __init__(self, type: str, value: int, duration: int, icon: pygame.Surface = None, heal_per_turn: int = 0):
        self.type = type
        self.value = value
        self.duration = duration
        self.icon = icon
        self.heal_per_turn = heal_per_turn  # Amount to heal per turn if this is a healing effect
    
    def update(self) -> bool:
        self.duration -= 1
        return self.duration > 0 