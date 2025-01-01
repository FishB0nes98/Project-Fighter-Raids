import pygame
from typing import List, Optional, Tuple
from items.base_item import Item

class LootWindow:
    # Colors
    BG_COLOR = (32, 36, 44, 240)  # Dark background with slight transparency
    BORDER_COLOR = (64, 68, 76)
    INNER_BORDER_COLOR = (80, 84, 92)
    TEXT_COLOR = (240, 240, 240)
    BUTTON_BG_COLOR = (48, 52, 64)
    BUTTON_HOVER_COLOR = (72, 76, 88)
    BUTTON_BORDER_COLOR = (96, 100, 108)
    BUTTON_TEXT_COLOR = (220, 220, 220)
    
    def __init__(self, x: int, y: int, width: int = 500, height: int = 800):
        self.rect = pygame.Rect(x, y, width, height)
        self.items: List[Item] = []
        self.font = pygame.font.Font(None, 26)
        self.title_font = pygame.font.Font(None, 32)
        self.is_dragging = False
        self.drag_offset = (0, 0)
        
        # Create surfaces
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.background = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Pre-render title
        self.title_surface = self.title_font.render("Loot Dropped!", True, self.TEXT_COLOR)
        self.title_rect = self.title_surface.get_rect(x=10, y=5)
        
        # Button dimensions
        self.button_width = 100
        self.button_height = 30
        self.button_spacing = 10
        
        # Item display properties
        self.item_height = 70
        self.item_padding = 8
        self.hovered_item = None
        
        # Keep track of which items have been decided on
        self.kept_items: List[bool] = []
    
    def set_items(self, items: List[Item]):
        """Set the items to be displayed in the loot window."""
        self.items = items
        self.kept_items = [None] * len(items)  # None = undecided, True = kept, False = left
    
    def handle_event(self, event: pygame.event.Event) -> List[Item]:
        """Handle events and return a list of items that were kept."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.rect.collidepoint(event.pos):
                    # Check if clicking title bar for dragging
                    title_bar = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 35)
                    if title_bar.collidepoint(event.pos):
                        self.is_dragging = True
                        mouse_x, mouse_y = event.pos
                        self.drag_offset = (self.rect.x - mouse_x, self.rect.y - mouse_y)
                    else:
                        # Check button clicks
                        rel_x = event.pos[0] - self.rect.x
                        rel_y = event.pos[1] - self.rect.y
                        
                        for i, item in enumerate(self.items):
                            if self.kept_items[i] is not None:
                                continue  # Skip items already decided on
                            
                            item_y = 40 + i * (self.item_height + self.item_padding)
                            
                            # Keep button
                            keep_rect = pygame.Rect(
                                self.rect.width - 2 * (self.button_width + self.button_spacing),
                                item_y + (self.item_height - self.button_height) // 2,
                                self.button_width,
                                self.button_height
                            )
                            if keep_rect.collidepoint(rel_x, rel_y):
                                self.kept_items[i] = True
                                print(f"[DEBUG] Keeping item: {item.name} (stack: {item.stack_count})")  # Debug print
                            
                            # Leave button
                            leave_rect = pygame.Rect(
                                self.rect.width - (self.button_width + self.button_spacing),
                                item_y + (self.item_height - self.button_height) // 2,
                                self.button_width,
                                self.button_height
                            )
                            if leave_rect.collidepoint(rel_x, rel_y):
                                self.kept_items[i] = False
                                print(f"[DEBUG] Leaving item: {item.name}")  # Debug print
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False
        
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                mouse_x, mouse_y = event.pos
                self.rect.x = mouse_x + self.drag_offset[0]
                self.rect.y = mouse_y + self.drag_offset[1]
                
                # Keep within screen bounds
                screen = pygame.display.get_surface()
                self.rect.clamp_ip(screen.get_rect())
            
            # Update hovered item for tooltip
            rel_x = event.pos[0] - self.rect.x
            rel_y = event.pos[1] - self.rect.y
            self.hovered_item = None
            
            for i, item in enumerate(self.items):
                item_y = 40 + i * (self.item_height + self.item_padding)
                item_rect = pygame.Rect(10, item_y, self.rect.width - 20, self.item_height)
                if item_rect.collidepoint(rel_x, rel_y):
                    self.hovered_item = item
                    break
        
        # Return kept items if all items have been decided
        if all(decision is not None for decision in self.kept_items):
            kept = [item for item, kept in zip(self.items, self.kept_items) if kept]
            print(f"[DEBUG] All items decided. Kept items: {[item.name for item in kept]}")  # Debug print
            return kept
        return None
    
    def draw(self, screen: pygame.Surface):
        # Clear surfaces
        self.surface.fill((0, 0, 0, 0))
        self.background.fill(self.BG_COLOR)
        
        # Draw title bar background
        title_bar = pygame.Rect(0, 0, self.rect.width, 35)
        pygame.draw.rect(self.background, self.BORDER_COLOR, title_bar)
        
        # Draw border with inner shadow effect
        border_rect = self.background.get_rect()
        pygame.draw.rect(self.background, self.BORDER_COLOR, border_rect, width=2, border_radius=8)
        
        # Draw subtle inner shadow
        shadow_rect = border_rect.inflate(-4, -4)
        pygame.draw.rect(self.background, (20, 24, 32, 100), shadow_rect, width=2, border_radius=6)
        
        # Track hovered item for tooltip
        hovered_item = None
        
        # Draw items
        for i, item in enumerate(self.items):
            item_y = 40 + i * (self.item_height + self.item_padding)
            
            # Draw item background
            item_rect = pygame.Rect(10, item_y, self.rect.width - 20, self.item_height)
            pygame.draw.rect(self.surface, self.BUTTON_BG_COLOR, item_rect, border_radius=6)
            pygame.draw.rect(self.surface, self.BUTTON_BORDER_COLOR, item_rect, width=2, border_radius=6)
            
            # Draw item icon
            icon_size = self.item_height - 20
            scaled_icon = pygame.transform.scale(item.icon, (icon_size, icon_size))
            self.surface.blit(scaled_icon, (20, item_y + 10))
            
            # Draw stack count if more than 1
            if item.stack_count > 1:
                stack_text = str(item.stack_count)
                stack_font = pygame.font.Font(None, 20)  # Smaller font for stack number
                # Draw shadow
                stack_shadow = stack_font.render(stack_text, True, (0, 0, 0))
                self.surface.blit(stack_shadow, (20 + scaled_icon.get_width() - 12, item_y + 10 + scaled_icon.get_height() - 11))
                # Draw text
                stack_surface = stack_font.render(stack_text, True, (255, 255, 255))
                self.surface.blit(stack_surface, (20 + scaled_icon.get_width() - 13, item_y + 10 + scaled_icon.get_height() - 12))
            
            # Draw item name and rarity with rarity color
            rarity_color = item.get_rarity_color()
            name_surface = self.font.render(item.name, True, rarity_color)
            rarity_surface = self.font.render(item.rarity, True, rarity_color)
            self.surface.blit(name_surface, (icon_size + 30, item_y + 15))
            self.surface.blit(rarity_surface, (icon_size + 30, item_y + 40))
            
            if self.kept_items[i] is None:
                # Draw Keep button
                keep_rect = pygame.Rect(
                    self.rect.width - 2 * (self.button_width + self.button_spacing),
                    item_y + (self.item_height - self.button_height) // 2,
                    self.button_width,
                    self.button_height
                )
                pygame.draw.rect(self.surface, self.BUTTON_BG_COLOR, keep_rect, border_radius=4)
                pygame.draw.rect(self.surface, self.BUTTON_BORDER_COLOR, keep_rect, width=2, border_radius=4)
                
                keep_text = self.font.render("Keep", True, self.BUTTON_TEXT_COLOR)
                text_rect = keep_text.get_rect(center=keep_rect.center)
                self.surface.blit(keep_text, text_rect)
                
                # Draw Leave button
                leave_rect = pygame.Rect(
                    self.rect.width - (self.button_width + self.button_spacing),
                    item_y + (self.item_height - self.button_height) // 2,
                    self.button_width,
                    self.button_height
                )
                pygame.draw.rect(self.surface, self.BUTTON_BG_COLOR, leave_rect, border_radius=4)
                pygame.draw.rect(self.surface, self.BUTTON_BORDER_COLOR, leave_rect, width=2, border_radius=4)
                
                leave_text = self.font.render("Leave", True, self.BUTTON_TEXT_COLOR)
                text_rect = leave_text.get_rect(center=leave_rect.center)
                self.surface.blit(leave_text, text_rect)
            else:
                # Draw decision text
                decision_text = "Kept" if self.kept_items[i] else "Left"
                text_surface = self.font.render(decision_text, True, self.BUTTON_TEXT_COLOR)
                text_rect = text_surface.get_rect(
                    right=self.rect.width - 20,
                    centery=item_y + self.item_height // 2
                )
                self.surface.blit(text_surface, text_rect)
            
            # Update item position for tooltip
            item.position = (self.rect.x + 10, self.rect.y + item_y)
            # Update hover state for tooltip
            mouse_pos = pygame.mouse.get_pos()
            item_rect = pygame.Rect(item.position[0], item.position[1], self.rect.width - 20, self.item_height)
            if item_rect.collidepoint(mouse_pos):
                hovered_item = item
        
        # Combine surfaces
        screen.blit(self.background, self.rect)
        screen.blit(self.surface, self.rect)
        
        # Draw title with shadow
        title_shadow_pos = (self.rect.x + 11, self.rect.y + 6)
        title_shadow = self.title_font.render("Loot Dropped!", True, (0, 0, 0))
        screen.blit(title_shadow, title_shadow_pos)
        
        title_pos = (self.rect.x + 10, self.rect.y + 5)
        screen.blit(self.title_surface, title_pos)
        
        # Draw tooltip for hovered item after everything else
        if hovered_item:
            # Position tooltip to the right of the loot window
            original_position = hovered_item.position
            hovered_item.position = (self.rect.right + 10, self.rect.y + 40)  # 40 pixels down from top to align with content
            hovered_item.is_hovered = True
            hovered_item.draw_tooltip(screen)
            hovered_item.is_hovered = False
            # Restore original position
            hovered_item.position = original_position 