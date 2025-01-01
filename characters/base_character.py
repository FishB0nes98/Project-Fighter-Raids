from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, TYPE_CHECKING
import pygame
from pathlib import Path
import math
import random
from PIL import Image

if TYPE_CHECKING:
    from abilities.base_ability import Ability

@dataclass
class DamageText:
    # Class-level caches
    _text_cache = {}
    _shadow_cache = {}
    _scaled_cache = {}
    _max_cache_size = 50  # Maximum number of cached entries per cache
    _max_active_texts = 8  # Maximum number of active floating texts per character
    _scale_precision = 2  # Round scale to 2 decimal places to reduce unique cache entries
    
    value: int
    position: Tuple[float, float]
    velocity: float = -3.0  # Faster upward movement
    lifetime: int = 45  # Shorter, snappier duration
    alpha: int = 255
    scale: float = 1.0  # For bounce effect
    color: Tuple[int, int, int] = (255, 80, 80)  # Default to damage color
    _rendered_text: Optional[pygame.Surface] = None
    _rendered_shadow: Optional[pygame.Surface] = None
    _scaled_text: Optional[pygame.Surface] = None
    _scaled_shadow: Optional[pygame.Surface] = None
    _last_scale: float = 1.0
    
    @classmethod
    def _clean_cache(cls, cache_dict):
        """Remove oldest entries if cache is too large."""
        while len(cache_dict) > cls._max_cache_size:
            cache_dict.pop(next(iter(cache_dict)))
    
    def render_text(self, font: pygame.font.Font):
        """Pre-render the text surface and shadow for reuse."""
        key = (str(self.value), self.color)
        
        # Try to get from cache first
        if key in DamageText._text_cache:
            self._rendered_text = DamageText._text_cache[key]
            self._rendered_shadow = DamageText._shadow_cache[key]
            return
        
        # Create new surfaces if not in cache
        self._rendered_text = font.render(str(self.value), True, self.color)
        self._rendered_shadow = font.render(str(self.value), True, (0, 0, 0))
        
        # Add to cache
        DamageText._text_cache[key] = self._rendered_text
        DamageText._shadow_cache[key] = self._rendered_shadow
        
        # Clean cache if needed
        self._clean_cache(DamageText._text_cache)
        self._clean_cache(DamageText._shadow_cache)
    
    def get_scaled_surfaces(self, scale_func) -> Tuple[pygame.Surface, pygame.Surface]:
        """Get or create scaled surfaces."""
        if self._rendered_text is None:
            return None, None
            
        # Round scale to reduce unique cache entries
        rounded_scale = round(self.scale, self._scale_precision)
        
        # Create cache key
        key = (id(self._rendered_text), rounded_scale)
        
        # Check if we have cached scaled surfaces
        if key in DamageText._scaled_cache and abs(self._last_scale - rounded_scale) <= 0.01:
            return DamageText._scaled_cache[key]
        
        # Create new scaled surfaces
        scaled_text = scale_func(
            self._rendered_text,
            (int(self._rendered_text.get_width() * rounded_scale),
             int(self._rendered_text.get_height() * rounded_scale))
        )
        scaled_shadow = scale_func(
            self._rendered_shadow,
            (int(self._rendered_shadow.get_width() * rounded_scale),
             int(self._rendered_shadow.get_height() * rounded_scale))
        )
        
        # Cache the new surfaces
        DamageText._scaled_cache[key] = (scaled_text, scaled_shadow)
        self._last_scale = rounded_scale
        
        # Clean cache if needed
        self._clean_cache(DamageText._scaled_cache)
        
        return scaled_text, scaled_shadow
    
    def cleanup(self):
        """Clean up surfaces when text is removed."""
        self._rendered_text = None
        self._rendered_shadow = None
        self._scaled_text = None
        self._scaled_shadow = None

@dataclass
class Stats:
    max_hp: int
    current_hp: int
    max_mana: int
    current_mana: int
    attack: int
    defense: int
    speed: int

@dataclass
class StatusEffect:
    def __init__(self, type: str, value: int, duration: int, icon: Optional[pygame.Surface] = None):
        self.type = type
        self.value = value
        self.duration = duration
        self.icon = icon
        self.heal_per_turn = 0  # Default to 0 for non-healing buffs
    
    def update(self) -> bool:
        self.duration -= 1
        return self.duration > 0

class Character:
    # Colors
    HEALTH_BG_COLOR = (40, 44, 52)
    HEALTH_BORDER_COLOR = (60, 64, 72)
    MANA_BG_COLOR = (40, 44, 52)
    MANA_BORDER_COLOR = (60, 64, 72)
    MANA_COLOR = (64, 156, 255)  # Bright blue
    ABILITY_BG_COLOR = (48, 52, 64)
    ABILITY_BORDER_COLOR = (80, 84, 96)
    DAMAGE_COLOR = (255, 80, 80)
    HEAL_COLOR = (80, 255, 120)
    
    # Class-level caches
    _flash_surface_cache = {}
    _bar_cache = {}  # Cache for HP/mana bars
    _icon_cache = {}  # Cache for buff/debuff icons
    _font_cache = {}  # Cache for rendered text
    
    def __init__(self, name: str, stats: Stats, image_path: str):
        self.name = name
        self.stats = stats
        self.abilities: List[Ability] = []
        self.buffs: List[StatusEffect] = []
        self.debuffs = []
        self.floating_texts: List[DamageText] = []
        self.inventory = None  # Will be set later
        self.loot_processed = False  # Initialize loot_processed flag
        
        # Load and scale character image using PIL for high quality resizing
        pil_image = Image.open(str(Path(image_path)))
        pil_image = pil_image.convert('RGBA')  # Ensure RGBA mode for transparency
        pil_image = pil_image.resize((240, 333), Image.Resampling.LANCZOS)  # High quality resize
        
        # Convert PIL image to Pygame surface
        image_data = pil_image.tobytes()
        pygame_image = pygame.image.fromstring(image_data, pil_image.size, 'RGBA')
        
        self.image = pygame_image
        self.original_image = self.image.copy()
        
        # Position will be set by the game engine
        self.position = (0, 0)
        
        # UI constants
        self.HP_BAR_WIDTH = 240
        self.HP_BAR_HEIGHT = 24
        self.MANA_BAR_WIDTH = 240
        self.MANA_BAR_HEIGHT = 20  # Slightly smaller than HP bar
        self.ABILITY_ICON_SIZE = 48
        self.ABILITY_SPACING = 16
        self.BUFF_ICON_SIZE = 32
        self.BUFF_SPACING = 4
        
        # Pre-render bar backgrounds
        self._create_bar_backgrounds()
        
        # Load fonts
        self.damage_font = pygame.font.Font(None, 36)
        self.hp_font = pygame.font.Font(None, 24)
        
        # Cache keys for optimization
        self._last_hp_text = None
        self._last_mana_text = None
        
        # Damage flash effect
        self.flash_duration = 10  # Shorter, snappier flash
        self.flash_timer = 0
        self.is_flashing = False
        
        # Floating text batch
        self.floating_text_batch: Dict[int, List[DamageText]] = {}  # Group texts by frame
        self.current_frame = 0
    
    def _create_bar_backgrounds(self):
        """Create cached bar backgrounds."""
        # HP bar background
        hp_key = ("hp_bg", self.HP_BAR_WIDTH, self.HP_BAR_HEIGHT)
        if hp_key not in Character._bar_cache:
            hp_bg = pygame.Surface((self.HP_BAR_WIDTH + 4, self.HP_BAR_HEIGHT + 4), pygame.SRCALPHA)
            # Border
            pygame.draw.rect(hp_bg, self.HEALTH_BORDER_COLOR, 
                           hp_bg.get_rect(), border_radius=6)
            # Inner background
            pygame.draw.rect(hp_bg, self.HEALTH_BG_COLOR, 
                           pygame.Rect(2, 2, self.HP_BAR_WIDTH, self.HP_BAR_HEIGHT), 
                           border_radius=5)
            Character._bar_cache[hp_key] = hp_bg
        
        # Mana bar background
        mana_key = ("mana_bg", self.MANA_BAR_WIDTH, self.MANA_BAR_HEIGHT)
        if mana_key not in Character._bar_cache:
            mana_bg = pygame.Surface((self.MANA_BAR_WIDTH + 4, self.MANA_BAR_HEIGHT + 4), pygame.SRCALPHA)
            # Border
            pygame.draw.rect(mana_bg, self.MANA_BORDER_COLOR, 
                           mana_bg.get_rect(), border_radius=6)
            # Inner background
            pygame.draw.rect(mana_bg, self.MANA_BG_COLOR, 
                           pygame.Rect(2, 2, self.MANA_BAR_WIDTH, self.MANA_BAR_HEIGHT), 
                           border_radius=5)
            Character._bar_cache[mana_key] = mana_bg
    
    def _get_text_surface(self, text: str, color: tuple) -> pygame.Surface:
        """Get cached text surface."""
        key = (text, color)
        if key not in Character._font_cache:
            text_surface = self.hp_font.render(text, True, color)
            Character._font_cache[key] = text_surface
            # Clean cache if too large
            if len(Character._font_cache) > 100:
                Character._font_cache.pop(next(iter(Character._font_cache)))
        return Character._font_cache[key]
    
    def _get_scaled_icon(self, icon: pygame.Surface, size: int) -> pygame.Surface:
        """Get cached scaled icon."""
        key = (id(icon), size)
        if key not in Character._icon_cache:
            # Convert surface to 32-bit RGBA if it isn't already
            if icon.get_bitsize() != 32:
                converted = icon.convert_alpha()
            else:
                converted = icon
            
            # Now scale the converted surface
            scaled = pygame.transform.smoothscale(converted, (size, size))
            Character._icon_cache[key] = scaled
            # Clean cache if too large
            if len(Character._icon_cache) > 50:
                Character._icon_cache.pop(next(iter(Character._icon_cache)))
        return Character._icon_cache[key]
    
    @staticmethod
    def high_quality_scale(surface: pygame.Surface, size: tuple) -> pygame.Surface:
        """Scale a Pygame surface using high quality PIL resizing."""
        # Convert Pygame surface to PIL Image
        surface_string = pygame.image.tostring(surface, 'RGBA')
        pil_image = Image.frombytes('RGBA', surface.get_size(), surface_string)
        
        # Use high quality resize
        pil_image = pil_image.resize(size, Image.Resampling.LANCZOS)
        
        # Convert back to Pygame surface
        return pygame.image.fromstring(pil_image.tobytes(), pil_image.size, 'RGBA')
        
    def add_ability(self, ability):
        if len(self.abilities) < 4:
            ability.icon = pygame.transform.scale(ability.icon, (self.ABILITY_ICON_SIZE, self.ABILITY_ICON_SIZE))
            self.abilities.append(ability)
    
    def is_alive(self) -> bool:
        return self.stats.current_hp > 0
    
    def take_damage(self, amount: int):
        # Apply damage increase from attacker's buffs (this should be done before calling take_damage)
        
        # Check for crystallize buff and apply damage increase if present
        for buff in self.buffs:
            if hasattr(buff, 'on_damage_taken'):
                amount = buff.on_damage_taken(amount)
        
        # First apply damage reduction from buffs (percentage reduction)
        damage_reduction = self.get_damage_reduction()
        after_reduction = max(1, int(amount * (1 - damage_reduction / 100)))
        
        # Then apply defense and defense buffs
        total_defense = self.stats.defense + self.get_defense_bonus()
        final_damage = max(1, after_reduction - total_defense)
        
        self.stats.current_hp -= final_damage
        
        # Create damage text only if we don't have too many active texts
        total_active_texts = len(self.floating_texts)
        for batch in self.floating_text_batch.values():
            total_active_texts += len(batch)
        
        if total_active_texts < DamageText._max_active_texts:
            # Create damage text
            damage_text = DamageText(
                value=final_damage,
                position=(self.position[0] + self.image.get_width() // 2,
                         self.position[1] + self.image.get_height() // 2),
                color=self.DAMAGE_COLOR
            )
            damage_text.render_text(self.damage_font)  # Pre-render the text
            
            # Add to current frame's batch
            if self.current_frame not in self.floating_text_batch:
                self.floating_text_batch[self.current_frame] = []
            self.floating_text_batch[self.current_frame].append(damage_text)
        
        # Start damage flash effect
        self.flash_timer = self.flash_duration
        self.is_flashing = True
        
        # Handle death
        if self.stats.current_hp <= 0:
            print(f"\n{self.name} has died! Type: {type(self)}")
            print(f"Loot processed flag: {self.loot_processed}")
            
            # Make the character invisible
            self.image.set_alpha(0)
            # Log death message
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                death_message = f"{self.name} has been defeated!"
                GameEngine.instance.battle_log.add_message(death_message, GameEngine.instance.battle_log.TEXT_COLOR)
                
                # Handle loot drops
                print(f"Processing loot for {self.name}...")
                GameEngine.instance.handle_character_death(self)
                print(f"Loot processing complete. Loot processed flag: {self.loot_processed}\n")
                
                # Remove dead character from stage's bosses list
                if GameEngine.instance.stage_manager.current_stage:
                    stage = GameEngine.instance.stage_manager.current_stage
                    if self in stage.bosses:
                        stage.bosses.remove(self)
        return final_damage
    
    def get_damage_reduction(self) -> float:
        """Get total damage reduction from all buffs"""
        total_reduction = 0
        for buff in self.buffs:
            if buff.type == "damage_reduction" or buff.type == "ice_wall" or buff.type == "sun_protection":
                if hasattr(buff, 'get_damage_reduction'):
                    total_reduction += buff.get_damage_reduction()
                else:
                    total_reduction += buff.value
        return min(total_reduction, 90)  # Cap at 90% damage reduction
    
    def heal(self, amount: int):
        # Apply healing increase from buffs
        original_amount = amount
        for buff in self.buffs:
            if hasattr(buff, 'apply_healing_increase'):
                amount = buff.apply_healing_increase(amount)

        # Get the effective max HP (including any bonus HP)
        effective_max_hp = self.stats.max_hp
        for buff in self.buffs:
            if hasattr(buff, 'bonus_hp'):
                effective_max_hp += buff.bonus_hp

        # Calculate heal amount considering effective max HP
        heal_amount = min(amount, effective_max_hp - self.stats.current_hp)
        self.stats.current_hp += heal_amount
        
        # Create heal text
        heal_text = DamageText(
            value=heal_amount,
            position=(self.position[0] + self.image.get_width() // 2,
                     self.position[1] + self.image.get_height() // 2),
            color=self.HEAL_COLOR
        )
        heal_text.render_text(self.damage_font)  # Pre-render the text
        
        # Add to current frame's batch
        if self.current_frame not in self.floating_text_batch:
            self.floating_text_batch[self.current_frame] = []
        self.floating_text_batch[self.current_frame].append(heal_text)
        
        return heal_amount
    
    def add_buff(self, buff):
        """Add a buff to the character"""
        # Check if buff should replace an existing one
        for i, existing_buff in enumerate(self.buffs):
            if hasattr(existing_buff, 'name') and hasattr(buff, 'name') and existing_buff.name == buff.name:
                # Don't replace non-removable buffs
                if hasattr(existing_buff, 'is_removable') and not existing_buff.is_removable:
                    return
                # Call on_remove for the old buff
                if hasattr(existing_buff, 'on_remove'):
                    existing_buff.on_remove(self)
                self.buffs[i] = buff
                break
        else:
            self.buffs.append(buff)
        
        # Call on_apply if the buff has it
        if hasattr(buff, 'on_apply'):
            buff.on_apply(self)
    
    def add_debuff(self, debuff):
        """Add a debuff to the character"""
        # Check if debuff should replace an existing one
        for i, existing_debuff in enumerate(self.debuffs):
            if hasattr(existing_debuff, 'name') and hasattr(debuff, 'name') and existing_debuff.name == debuff.name:
                # Don't replace non-removable debuffs
                if hasattr(existing_debuff, 'is_removable') and not existing_debuff.is_removable:
                    return
                # Call on_remove for the old debuff
                if hasattr(existing_debuff, 'on_remove'):
                    existing_debuff.on_remove(self)
                self.debuffs[i] = debuff
                break
        else:
            self.debuffs.append(debuff)
        
        # Call on_apply if the debuff has it
        if hasattr(debuff, 'on_apply'):
            debuff.on_apply(self)
    
    def update(self):
        # Update damage flash with pulsing effect
        if self.flash_timer > 0:
            self.flash_timer -= 1
            flash_intensity = int((math.sin(self.flash_timer * 0.8) * 0.5 + 0.5) * 255)
            
            # Get or create flash surface from cache
            size_key = (self.image.get_width(), self.image.get_height())
            if size_key not in Character._flash_surface_cache:
                Character._flash_surface_cache[size_key] = pygame.Surface(size_key).convert_alpha()
            
            flash_surface = Character._flash_surface_cache[size_key]
            flash_surface.fill((255, 0, 0, flash_intensity))
            
            if not hasattr(self, 'flash_image'):
                self.flash_image = self.original_image.copy()
            else:
                self.flash_image.blit(self.original_image, (0, 0))
            
            self.flash_image.blit(flash_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = self.flash_image
            
            if self.flash_timer == 0:
                self.is_flashing = False
                self.image = self.original_image.copy()
        
        # Update floating damage texts with bounce effect
        self.current_frame += 1
        
        # Add any batched texts from 3 frames ago to the active texts
        if self.current_frame - 3 in self.floating_text_batch:
            self.floating_texts.extend(self.floating_text_batch[self.current_frame - 3])
            del self.floating_text_batch[self.current_frame - 3]
        
        # Update active texts
        new_texts = []
        for text in self.floating_texts:
            text.position = (text.position[0], text.position[1] + text.velocity)
            text.lifetime -= 1
            
            if text.lifetime <= 0:
                text.cleanup()  # Clean up surfaces when text expires
                continue
            
            # Bounce effect
            progress = 1 - (text.lifetime / 45)  # Normalized time
            text.scale = 1 + math.sin(progress * math.pi) * 0.3  # Scale varies from 1.0 to 1.3
            
            # Fade out
            if text.lifetime < 20:
                text.alpha = int((text.lifetime / 20) * 255)
            
            new_texts.append(text)
        
        self.floating_texts = new_texts
        
        # Clean up old batches
        current_time = self.current_frame
        old_batches = {k: v for k, v in self.floating_text_batch.items() 
                      if current_time - k > 10}
        # Clean up surfaces in old batches
        for batch in old_batches.values():
            for text in batch:
                text.cleanup()
        # Remove old batches
        self.floating_text_batch = {k: v for k, v in self.floating_text_batch.items() 
                                  if current_time - k <= 10}
    
    def end_turn(self):
        """Update buffs and debuffs at the end of turn"""
        # Apply heal per turn from buffs
        for buff in self.buffs:
            if hasattr(buff, 'heal_per_turn') and buff.heal_per_turn > 0:
                heal_amount = buff.heal_per_turn
                # Apply healing modifiers from buffs
                for healing_buff in self.buffs:
                    if hasattr(healing_buff, 'modify_healing_received'):
                        heal_amount = healing_buff.modify_healing_received(heal_amount)
                self.heal(heal_amount)

        # Update buff durations
        self.buffs = [buff for buff in self.buffs if buff.update()]
        self.debuffs = [debuff for debuff in self.debuffs if debuff.update()]
    
    def draw(self, screen: pygame.Surface):
        # Don't draw anything if the character is dead
        if not self.is_alive():
            return
            
        # Draw selection indicator if this is the selected character
        from engine.game_engine import GameEngine
        if (GameEngine.instance and 
            GameEngine.instance.game_state.selected_character_index < len(GameEngine.instance.stage_manager.player_characters) and
            GameEngine.instance.stage_manager.player_characters[GameEngine.instance.game_state.selected_character_index] == self):
            # Draw a modern highlight effect around the character
            # First draw a larger outer glow
            glow_size = 8
            glow_rect = pygame.Rect(self.position[0] - glow_size, self.position[1] - glow_size,
                                  self.image.get_width() + glow_size * 2, self.image.get_height() + glow_size * 2)
            # Draw multiple layers of decreasing size for a smooth glow effect
            for i in range(4):
                alpha = 40 - i * 10  # Decrease alpha for outer layers
                current_rect = glow_rect.inflate(-i * 2, -i * 2)
                glow_surface = pygame.Surface((current_rect.width, current_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (255, 255, 100, alpha), glow_surface.get_rect(), border_radius=10)
                screen.blit(glow_surface, current_rect)
            
            # Draw a thin bright border
            border_rect = pygame.Rect(self.position[0] - 2, self.position[1] - 2,
                                    self.image.get_width() + 4, self.image.get_height() + 4)
            pygame.draw.rect(screen, (255, 255, 100), border_rect, width=2, border_radius=8)
        
        # Draw character image
        screen.blit(self.image, self.position)
        
        # Draw floating texts
        for text in self.floating_texts:
            if text._rendered_text is None:
                text.render_text(self.damage_font)
            
            # Get scaled surfaces (cached)
            scaled_text, scaled_shadow = text.get_scaled_surfaces(self.high_quality_scale)
            if scaled_text is None or scaled_shadow is None:
                continue
            
            # Set alpha for fade out
            if text.alpha != 255:  # Only set alpha if it's not fully opaque
                scaled_text.set_alpha(text.alpha)
                scaled_shadow.set_alpha(text.alpha)
            
            # Calculate positions
            text_pos = (text.position[0] - scaled_text.get_width() // 2,
                       text.position[1] - scaled_text.get_height() // 2)
            shadow_pos = (text_pos[0] + 2, text_pos[1] + 2)
            
            # Draw shadow then text
            screen.blit(scaled_shadow, shadow_pos)
            screen.blit(scaled_text, text_pos)
        
        # Draw HP bar
        hp_ratio = min(self.stats.current_hp / self.stats.max_hp, 1.5)
        hp_bar_pos = (self.position[0], self.position[1] + self.image.get_height() + 10)
        
        # Draw HP bar background
        hp_bg_key = ("hp_bg", self.HP_BAR_WIDTH, self.HP_BAR_HEIGHT)
        screen.blit(Character._bar_cache[hp_bg_key], 
                   (hp_bar_pos[0]-2, hp_bar_pos[1]-2))
        
        # Draw HP bar fill
        hp_fill_rect = pygame.Rect(hp_bar_pos[0], hp_bar_pos[1],
                                 int(self.HP_BAR_WIDTH * hp_ratio), self.HP_BAR_HEIGHT)
        # Calculate health bar color based on percentage
        if hp_ratio > 1:  # Overheal
            bar_color = (100, 255, 100)  # Bright green
        else:
            r = min(255, int(255 * (1 - hp_ratio) * 2))
            g = min(255, int(255 * hp_ratio * 2))
            bar_color = (r, g, 50)
        pygame.draw.rect(screen, bar_color, hp_fill_rect, border_radius=4)
        
        # Draw HP text
        hp_text = f"{self.stats.current_hp}/{self.stats.max_hp}"
        if hp_text != self._last_hp_text:
            self._last_hp_text = hp_text
            hp_surface = self._get_text_surface(hp_text, (255, 255, 255))
        else:
            hp_surface = self._get_text_surface(hp_text, (255, 255, 255))
        hp_text_pos = (hp_bar_pos[0] + (self.HP_BAR_WIDTH - hp_surface.get_width()) // 2,
                      hp_bar_pos[1] + (self.HP_BAR_HEIGHT - hp_surface.get_height()) // 2)
        screen.blit(hp_surface, hp_text_pos)
        
        # Draw mana bar if character has mana
        if hasattr(self.stats, 'max_mana') and self.stats.max_mana > 0:
            mana_ratio = self.stats.current_mana / self.stats.max_mana
            mana_bar_pos = (hp_bar_pos[0], hp_bar_pos[1] + self.HP_BAR_HEIGHT + 5)
            
            # Draw mana bar background
            mana_bg_key = ("mana_bg", self.MANA_BAR_WIDTH, self.MANA_BAR_HEIGHT)
            screen.blit(Character._bar_cache[mana_bg_key], 
                       (mana_bar_pos[0]-2, mana_bar_pos[1]-2))
            
            # Draw mana bar fill
            mana_fill_rect = pygame.Rect(mana_bar_pos[0], mana_bar_pos[1],
                                       int(self.MANA_BAR_WIDTH * mana_ratio), self.MANA_BAR_HEIGHT)
            pygame.draw.rect(screen, self.MANA_COLOR, mana_fill_rect, border_radius=4)
            
            # Draw mana text
            mana_text = f"{self.stats.current_mana}/{self.stats.max_mana}"
            if mana_text != self._last_mana_text:
                self._last_mana_text = mana_text
                mana_surface = self._get_text_surface(mana_text, (255, 255, 255))
            else:
                mana_surface = self._get_text_surface(mana_text, (255, 255, 255))
            mana_text_pos = (mana_bar_pos[0] + (self.MANA_BAR_WIDTH - mana_surface.get_width()) // 2,
                           mana_bar_pos[1] + (self.MANA_BAR_HEIGHT - mana_surface.get_height()) // 2)
            screen.blit(mana_surface, mana_text_pos)
        
        # Draw ability icons
        ability_y = hp_bar_pos[1] + self.HP_BAR_HEIGHT + 5
        if hasattr(self.stats, 'max_mana') and self.stats.max_mana > 0:
            ability_y += self.MANA_BAR_HEIGHT + 5
        
        total_abilities_width = len(self.abilities) * self.ABILITY_ICON_SIZE + (len(self.abilities) - 1) * self.ABILITY_SPACING
        ability_start_x = self.position[0] + (self.HP_BAR_WIDTH - total_abilities_width) // 2
        
        # Check if stunned
        is_locked = any(hasattr(debuff, 'name') and debuff.name == "Stunned" for debuff in self.debuffs)
        
        for i, ability in enumerate(self.abilities):
            ability.position = (ability_start_x + i * (self.ABILITY_ICON_SIZE + self.ABILITY_SPACING), ability_y)
            
            # Draw ability background with border
            ability_border = pygame.Rect(ability.position[0]-2, ability.position[1]-2,
                                      self.ABILITY_ICON_SIZE+4, self.ABILITY_ICON_SIZE+4)
            pygame.draw.rect(screen, self.ABILITY_BORDER_COLOR, ability_border, border_radius=6)
            
            ability_bg = pygame.Rect(ability.position[0], ability.position[1],
                                  self.ABILITY_ICON_SIZE, self.ABILITY_ICON_SIZE)
            pygame.draw.rect(screen, self.ABILITY_BG_COLOR, ability_bg, border_radius=5)
            
            # Draw ability icon with caching
            scaled_icon = self._get_scaled_icon(ability.icon, self.ABILITY_ICON_SIZE)
            screen.blit(scaled_icon, ability.position)
            
            # Draw cooldown or locked overlay
            if not ability.is_available() or (is_locked and ability.name != "Spiritwalk"):
                cooldown_surface = pygame.Surface((self.ABILITY_ICON_SIZE, self.ABILITY_ICON_SIZE), pygame.SRCALPHA)
                cooldown_surface.fill((20, 20, 20, 200))
                screen.blit(cooldown_surface, ability.position)
                
                if not ability.is_available():
                    cooldown_text = str(ability.current_cooldown)
                    text_surface = self._get_text_surface(cooldown_text, (255, 255, 255))
                    text_pos = (ability.position[0] + (self.ABILITY_ICON_SIZE - text_surface.get_width()) // 2,
                              ability.position[1] + (self.ABILITY_ICON_SIZE - text_surface.get_height()) // 2)
                    screen.blit(text_surface, text_pos)
                elif is_locked and ability.name != "Spiritwalk":
                    lock_text = "X"
                    text_surface = self._get_text_surface(lock_text, (255, 80, 80))
                    text_pos = (ability.position[0] + (self.ABILITY_ICON_SIZE - text_surface.get_width()) // 2,
                              ability.position[1] + (self.ABILITY_ICON_SIZE - text_surface.get_height()) // 2)
                    screen.blit(text_surface, text_pos)
        
        # Draw buff/debuff icons
        BUFF_SIZE = 48  # Increased size for buff icons
        buff_x = self.position[0]  # Start from left edge
        buff_y = self.position[1]
        
        # Colors for tooltips
        TOOLTIP_BG_COLOR = (32, 36, 44, 240)  # Dark background with slight transparency
        TOOLTIP_BORDER_COLOR = (64, 68, 76)
        TOOLTIP_INNER_BORDER_COLOR = (80, 84, 92)
        TOOLTIP_TEXT_COLOR = (220, 220, 220)
        TOOLTIP_TITLE_COLOR = (255, 255, 255)
        TOOLTIP_SHADOW_COLOR = (0, 0, 0, 60)
        
        # Track mouse position for tooltips
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw buffs in top-left corner
        for i, buff in enumerate(self.buffs):
            if buff.icon:
                scaled_icon = self._get_scaled_icon(buff.icon, BUFF_SIZE)
                icon_x = buff_x + i * (BUFF_SIZE + 4)  # 4 pixels spacing
                buff_rect = pygame.Rect(icon_x, buff_y, BUFF_SIZE, BUFF_SIZE)
                screen.blit(scaled_icon, (icon_x, buff_y))
                
                # Draw duration
                duration_text = str(buff.duration)
                text_surface = self._get_text_surface(duration_text, (255, 255, 255))
                text_pos = (icon_x + (BUFF_SIZE - text_surface.get_width()) // 2,
                          buff_y + BUFF_SIZE + 4)
                screen.blit(text_surface, text_pos)
                
                # Draw tooltip if buff is hovered
                if buff_rect.collidepoint(mouse_pos):
                    # Prepare tooltip text
                    if buff.type == "damage_reduction" or buff.type == "ice_wall":
                        title = "Ice Wall"
                        description = f"Reduces damage taken by {buff.value}%"
                        if hasattr(buff, 'duration'):
                            description += f"\n{buff.duration} turns remaining"
                    elif buff.type == "heal_over_time":
                        title = "Healing"
                        description = f"Heals {buff.value} HP per turn"
                    elif buff.type == "defense":
                        title = "Defense Up"
                        description = f"Increases armor by {buff.value}"
                    elif buff.type == "stealth":
                        title = buff.get_tooltip_title() if hasattr(buff, 'get_tooltip_title') else "Stealth"
                        description = buff.get_tooltip_text() if hasattr(buff, 'get_tooltip_text') else "Character is stealthed"
                    elif buff.type == "custom":
                        title = buff.get_tooltip_title() if hasattr(buff, 'get_tooltip_title') else buff.name
                        description = buff.get_tooltip_text() if hasattr(buff, 'get_tooltip_text') else buff.description
                    else:
                        title = "Buff"
                        description = f"Increases stats by {buff.value}"
                    
                    self._draw_tooltip(screen, title, description, buff_rect)
        
        # Draw debuffs below buffs
        debuff_y = buff_y + BUFF_SIZE + 24  # More spacing between buffs and debuffs
        for i, debuff in enumerate(self.debuffs):
            if debuff.icon:
                scaled_icon = self._get_scaled_icon(debuff.icon, BUFF_SIZE)
                icon_x = buff_x + i * (BUFF_SIZE + 4)
                debuff_rect = pygame.Rect(icon_x, debuff_y, BUFF_SIZE, BUFF_SIZE)
                screen.blit(scaled_icon, (icon_x, debuff_y))
                
                # Draw duration
                duration_text = str(debuff.duration)
                text_surface = self._get_text_surface(duration_text, (255, 255, 255))
                text_pos = (icon_x + (BUFF_SIZE - text_surface.get_width()) // 2,
                          debuff_y + BUFF_SIZE + 4)
                screen.blit(text_surface, text_pos)
                
                # Draw tooltip if debuff is hovered
                if debuff_rect.collidepoint(mouse_pos):
                    # Prepare tooltip text
                    if hasattr(debuff, 'get_tooltip_title') and hasattr(debuff, 'get_tooltip_text'):
                        title = debuff.get_tooltip_title()
                        description = debuff.get_tooltip_text()
                    else:
                        title = "Debuff"
                        description = f"Decreases stats by {abs(debuff.value)}"
                    
                    self._draw_tooltip(screen, title, description, debuff_rect)
    
    def _draw_tooltip(self, screen: pygame.Surface, title: str, description: str, anchor_rect: pygame.Rect):
        """Draw a tooltip with the given title and description."""
        padding = 16
        line_spacing = 6
        
        # Create text surfaces with caching
        title_surface = self._get_text_surface(title, (255, 255, 255))
        
        # Handle multiline description
        desc_lines = description.split('\n')
        desc_surfaces = [self._get_text_surface(line, (220, 220, 220)) for line in desc_lines]
        
        # Calculate tooltip dimensions
        width = max(
            title_surface.get_width(),
            *[surface.get_width() for surface in desc_surfaces]
        ) + padding * 3
        
        height = (padding * 2 + title_surface.get_height() + line_spacing +
                 sum(surface.get_height() + line_spacing for surface in desc_surfaces))
        
        # Position tooltip above the icon
        x = anchor_rect.x
        y = anchor_rect.y - height - 10
        
        # Keep tooltip on screen
        if x + width > screen.get_width():
            x = screen.get_width() - width
        if y < 0:
            y = anchor_rect.bottom + 10
        
        # Draw tooltip shadow
        shadow_rect = pygame.Rect(x + 4, y + 4, width, height)
        pygame.draw.rect(screen, (0, 0, 0, 60), shadow_rect, border_radius=10)
        
        # Draw main tooltip background
        tooltip_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, (32, 36, 44, 240), tooltip_rect, border_radius=10)
        
        # Draw borders
        border_rect = tooltip_rect.inflate(2, 2)
        pygame.draw.rect(screen, (64, 68, 76), border_rect, width=2, border_radius=10)
        inner_border = tooltip_rect.inflate(-2, -2)
        pygame.draw.rect(screen, (80, 84, 92), inner_border, width=1, border_radius=9)
        
        # Draw title
        current_y = y + padding
        screen.blit(title_surface, (x + padding, current_y))
        current_y += title_surface.get_height() + line_spacing
        
        # Draw separator line
        separator_y = current_y - line_spacing//2
        pygame.draw.line(screen, (80, 84, 92),
                        (x + padding, separator_y),
                        (x + width - padding, separator_y))
        
        # Draw description lines
        for desc_surface in desc_surfaces:
            screen.blit(desc_surface, (x + padding, current_y))
            current_y += desc_surface.get_height() + line_spacing
    
    def get_defense_bonus(self) -> int:
        """Get total defense bonus from buffs"""
        defense_bonus = 0
        for buff in self.buffs:
            if buff.type == "defense":
                defense_bonus += buff.value
        return defense_bonus

    def restore_mana(self, amount: int):
        """Restore mana points to the character."""
        restore_amount = min(amount, self.stats.max_mana - self.stats.current_mana)
        self.stats.current_mana += restore_amount
        
        # Add floating mana text
        self.floating_texts.append(DamageText(
            value=restore_amount,
            position=(self.position[0] + self.image.get_width() // 2,
                     self.position[1] + self.image.get_height() // 2),
            color=self.MANA_COLOR  # Use the mana color for the floating text
        ))
        
        return restore_amount 

    def is_targetable(self) -> bool:
        """Return True if the character can be targeted"""
        # Check if character has stealth buff
        for buff in self.buffs:
            if buff.type == "stealth" and hasattr(buff, 'is_targetable') and not buff.is_targetable():
                return False
        return True 