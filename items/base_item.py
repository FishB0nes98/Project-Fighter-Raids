from typing import Optional, List, TYPE_CHECKING
import pygame
from pathlib import Path
from PIL import Image

if TYPE_CHECKING:
    from characters.base_character import Character

class Item:
    # Colors for tooltips
    TOOLTIP_BG_COLOR = (32, 36, 44, 240)  # Dark background with slight transparency
    TOOLTIP_BORDER_COLOR = (64, 68, 76)
    TOOLTIP_TEXT_COLOR = (240, 240, 240)
    
    # Rarity colors
    RARITY_COLORS = {
        "Common": (200, 200, 200),  # Light gray
        "Uncommon": (30, 255, 0),   # Green
        "Rare": (0, 112, 221),      # Blue
        "Epic": (163, 53, 238),     # Purple
        "Legendary": (255, 128, 0)   # Orange
    }
    
    def __init__(self, name: str, description: str, rarity: str, item_type: str, icon_path: str, max_stack: int = 1):
        self.name = name
        self.description = description
        self.rarity = rarity
        self.item_type = item_type
        self.max_stack = max_stack
        self.stack_count = 1
        
        # Load and scale item icon with high quality scaling
        pil_image = Image.open(str(Path(icon_path)))
        pil_image = pil_image.convert('RGBA')  # Ensure RGBA mode for transparency
        pil_image = pil_image.resize((50, 50), Image.Resampling.LANCZOS)  # High quality resize
        
        # Convert PIL image to Pygame surface
        image_data = pil_image.tobytes()
        self.icon = pygame.image.fromstring(image_data, pil_image.size, 'RGBA')
        self.icon = self.icon.convert_alpha()  # Convert for faster blitting
        
        # UI state
        self.is_hovered = False
        self.position = (0, 0)  # Will be set when drawn
        
        # Tooltip font
        self.tooltip_font = pygame.font.Font(None, 24)
        
        # Cooldown system
        self.cooldown = 0  # Base cooldown duration
        self.current_cooldown = 0  # Current cooldown remaining
        self.ends_turn = True  # Most items end the turn by default
        
    def handle_mouse_motion(self, mouse_pos: tuple[int, int], relative_pos: tuple[int, int]):
        """Handle mouse motion for tooltip display"""
        item_rect = pygame.Rect(relative_pos[0], relative_pos[1], self.icon.get_width(), self.icon.get_height())
        self.is_hovered = item_rect.collidepoint(mouse_pos)
        self.position = relative_pos
        
    def can_stack_with(self, other: 'Item') -> bool:
        """Check if this item can stack with another item."""
        return (self.name == other.name and 
                self.rarity == other.rarity and 
                self.item_type == other.item_type and 
                self.stack_count < self.max_stack)
    
    def add_to_stack(self, count: int) -> int:
        """
        Try to add count items to this stack.
        Returns the number of items that couldn't be added (remainder).
        """
        space_left = self.max_stack - self.stack_count
        can_add = min(space_left, count)
        self.stack_count += can_add
        return count - can_add
    
    def split_stack(self, count: int) -> Optional['Item']:
        """
        Split this stack and return a new item with the specified count.
        Returns None if count is invalid.
        """
        if count <= 0 or count >= self.stack_count:
            return None
        
        # Create new item with the split amount
        new_item = self.__class__(self.name, self.description, self.rarity, self.item_type, self.max_stack)
        new_item.stack_count = count
        self.stack_count -= count
        return new_item
        
    def get_tooltip(self) -> str:
        """Get the tooltip text for this item."""
        tooltip = f"{self.name}\n{self.rarity}\n{self.description}"
        if self.stack_count > 1:
            tooltip = f"x{self.stack_count} {tooltip}"
        return tooltip
    
    def draw_tooltip(self, screen: pygame.Surface):
        """Draw the item tooltip with cooldown information."""
        if not self.is_hovered:
            return
            
        padding = 16
        line_spacing = 6
        
        # Prepare text surfaces with shadows
        title_font = pygame.font.Font(None, 32)
        desc_font = pygame.font.Font(None, 26)
        detail_font = pygame.font.Font(None, 24)
        
        title_shadow = title_font.render(self.name, True, (0, 0, 0))
        title_surface = title_font.render(self.name, True, self.RARITY_COLORS.get(self.rarity, (255, 255, 255)))
        desc_surface = desc_font.render(self.description, True, (220, 220, 220))
        
        # Prepare effect text
        effect_lines = ["Effects:"]
        if self.cooldown > 0:
            effect_lines.append(f"• Cooldown: {self.cooldown} turns")
        if self.ends_turn:
            effect_lines.append("• Ends your turn")
        
        effect_surfaces = [detail_font.render(line, True, (220, 220, 220)) for line in effect_lines]
        
        # Calculate tooltip dimensions
        width = max(
            title_surface.get_width(),
            desc_surface.get_width(),
            *[surface.get_width() for surface in effect_surfaces]
        ) + padding * 3
        
        height = (padding * 2 + title_surface.get_height() + line_spacing +
                 desc_surface.get_height() + line_spacing * 2 +
                 sum(surface.get_height() + line_spacing for surface in effect_surfaces))
        
        # Position tooltip to the right of the item
        x = self.position[0] + self.icon.get_width() + 10
        y = self.position[1]
        
        # Keep tooltip on screen
        screen_rect = screen.get_rect()
        if x + width > screen_rect.width:
            x = self.position[0] - width - 10
        if y + height > screen_rect.height:
            y = screen_rect.height - height
        if y < 0:
            y = 0
        
        # Draw tooltip background with border
        tooltip_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, self.TOOLTIP_BG_COLOR, tooltip_rect, border_radius=10)
        pygame.draw.rect(screen, self.TOOLTIP_BORDER_COLOR, tooltip_rect, width=2, border_radius=10)
        
        # Draw title with shadow
        current_y = y + padding
        screen.blit(title_shadow, (x + padding + 1, current_y + 1))
        screen.blit(title_surface, (x + padding, current_y))
        current_y += title_surface.get_height() + line_spacing
        
        # Draw separator line
        pygame.draw.line(screen, self.TOOLTIP_BORDER_COLOR,
                        (x + padding, current_y - line_spacing//2),
                        (x + width - padding, current_y - line_spacing//2))
        
        # Draw description
        screen.blit(desc_surface, (x + padding, current_y))
        current_y += desc_surface.get_height() + line_spacing * 2
        
        # Draw effects
        for i, effect_surface in enumerate(effect_surfaces):
            # Draw shadow for each line
            shadow = detail_font.render(effect_lines[i], True, (0, 0, 0))
            screen.blit(shadow, (x + padding + 1, current_y + 1))
            screen.blit(effect_surface, (x + padding, current_y))
            current_y += effect_surface.get_height() + line_spacing
        
    def is_available(self) -> bool:
        """Check if the item can be used (cooldown)"""
        return self.current_cooldown == 0

    def update(self):
        """Update cooldown"""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

    def use(self, user: "Character", target: "Character") -> bool:
        """Base use method that handles cooldown and logging"""
        if not self.is_available():
            return False
            
        # Start cooldown
        self.current_cooldown = self.cooldown
        
        # Log item use
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"{user.name} uses {self.name} on {target.name}",
                GameEngine.instance.battle_log.TEXT_COLOR
            )
            
            # End turn if item is configured to do so
            if self.ends_turn:
                GameEngine.instance.game_state.is_player_turn = False
        
        return True

    def draw(self, screen: pygame.Surface):
        """Draw the item with cooldown overlay"""
        # Draw item icon
        screen.blit(self.icon, self.position)
        
        # Draw cooldown overlay if not available
        if not self.is_available():
            cooldown_surface = pygame.Surface(self.icon.get_size(), pygame.SRCALPHA)
            cooldown_surface.fill((0, 0, 0, 128))  # Semi-transparent black
            screen.blit(cooldown_surface, self.position)
            
            # Draw cooldown number
            font = pygame.font.Font(None, 36)
            text = font.render(str(self.current_cooldown), True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.position[0] + self.icon.get_width()//2,
                                            self.position[1] + self.icon.get_height()//2))
            screen.blit(text, text_rect)
        
        # Draw stack count if more than 1
        if self.stack_count > 1:
            font = pygame.font.Font(None, 24)
            text = font.render(str(self.stack_count), True, (255, 255, 255))
            text_rect = text.get_rect(bottomright=(self.position[0] + self.icon.get_width() - 2,
                                                 self.position[1] + self.icon.get_height() - 2))
            # Draw text shadow
            shadow = font.render(str(self.stack_count), True, (0, 0, 0))
            shadow_rect = text_rect.copy()
            shadow_rect.x += 1
            shadow_rect.y += 1
            screen.blit(shadow, shadow_rect)
            screen.blit(text, text_rect)

    def get_rarity_color(self) -> tuple:
        """Get the color associated with this item's rarity."""
        return self.RARITY_COLORS.get(self.rarity, self.TOOLTIP_TEXT_COLOR) 