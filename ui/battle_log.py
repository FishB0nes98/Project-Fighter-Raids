import pygame
from typing import List, Tuple
from collections import deque
import time

class BattleLog:
    # Colors
    BG_COLOR = (32, 36, 44, 240)  # Darker background with less transparency
    BORDER_COLOR = (64, 68, 76)
    TEXT_COLOR = (240, 240, 240)  # Brighter text
    DAMAGE_COLOR = (255, 96, 96)
    HEAL_COLOR = (96, 255, 96)
    MANA_COLOR = (64, 156, 255)
    BUFF_COLOR = (255, 215, 0)
    
    # Minimum dimensions
    MIN_WIDTH = 300
    MIN_HEIGHT = 200
    
    # Line spacing
    LINE_SPACING = 8  # Increased from 4
    TEXT_PADDING = 10  # Padding from edges
    
    # Class-level cache for rendered messages
    _message_cache = {}
    _max_cache_size = 100  # Maximum number of cached messages
    
    def __init__(self, x: int, y: int, width: int = 400, height: int = 300):
        self.rect = pygame.Rect(x, y, width, height)
        self.messages: deque[Tuple[str, tuple]] = deque(maxlen=15)  # Increased max messages
        self.font = pygame.font.Font(None, 20)  # Smaller font size
        self.is_dragging = False
        self.drag_offset = (0, 0)
        self.scroll_offset = 0
        self.is_resizing = False
        self.resize_offset = (0, 0)
        
        # Create surfaces
        self.log_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.background = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Pre-render title and background
        self.title_font = pygame.font.Font(None, 24)  # Smaller title font
        self.title_surface = self.title_font.render("Battle Log", True, self.TEXT_COLOR)
        self.title_shadow = self.title_font.render("Battle Log", True, (0, 0, 0))
        self.title_rect = self.title_surface.get_rect(x=10, y=5)
        
        # Initialize resize handle dimensions first
        self.resize_handle_size = 16
        self.resize_handle_rect = pygame.Rect(
            width - self.resize_handle_size,
            height - self.resize_handle_size,
            self.resize_handle_size,
            self.resize_handle_size
        )
        
        # Pre-render background after resize handle is initialized
        self._update_background()
    
    def _update_background(self):
        """Update background surface with current dimensions"""
        self.background = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        self.background.fill(self.BG_COLOR)
        
        # Draw title bar
        title_bar = pygame.Rect(0, 0, self.rect.width, 30)  # Shorter title bar
        pygame.draw.rect(self.background, (*self.BORDER_COLOR, 255), title_bar)
        
        # Draw main border
        border_rect = self.background.get_rect()
        pygame.draw.rect(self.background, (*self.BORDER_COLOR, 255), 
                        border_rect, width=2, border_radius=6)  # Smaller border radius
        
        # Draw inner shadow
        shadow_rect = border_rect.inflate(-4, -4)
        pygame.draw.rect(self.background, (20, 24, 32, 100), 
                        shadow_rect, width=2, border_radius=4)
        
        # Draw resize handle
        handle_rect = pygame.Rect(
            self.rect.width - self.resize_handle_size,
            self.rect.height - self.resize_handle_size,
            self.resize_handle_size,
            self.resize_handle_size
        )
        pygame.draw.lines(self.background, self.BORDER_COLOR, False, [
            (handle_rect.right - 12, handle_rect.bottom - 2),
            (handle_rect.right - 2, handle_rect.bottom - 12),
            (handle_rect.right - 2, handle_rect.bottom - 2)
        ], 2)
    
    def add_message(self, text: str, color: tuple = TEXT_COLOR):
        """Add a message to the battle log"""
        self.messages.append((text, color))
        # Reset scroll to bottom when new message arrives
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """Scroll to show the most recent messages"""
        total_height = sum(self.font.get_height() + self.LINE_SPACING for _ in self.messages)
        if total_height > self.rect.height - 35:
            self.scroll_offset = min(0, self.rect.height - total_height - 35)
    
    def _wrap_text(self, text: str, max_width: int, font: pygame.font.Font) -> List[str]:
        """Wrap text to fit within a given width."""
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        space_width = font.size(' ')[0]
        
        for word in words:
            word_surface = font.render(word, True, (0, 0, 0))
            word_width = word_surface.get_width()
            
            if current_width + word_width + (len(current_line) * space_width) <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _get_cached_message(self, text: str, color: tuple, max_width: int) -> List[Tuple[pygame.Surface, pygame.Surface]]:
        """Get or create cached message surfaces with wrapping."""
        key = (text, color, max_width)
        if key not in self._message_cache:
            # If cache is full, remove oldest entry
            if len(self._message_cache) >= self._max_cache_size:
                oldest_key = next(iter(self._message_cache))
                del self._message_cache[oldest_key]
            
            # Wrap text and render each line
            lines = self._wrap_text(text, max_width, self.font)
            rendered_lines = []
            
            for line in lines:
                shadow = self.font.render(line, True, (0, 0, 0))
                message = self.font.render(line, True, color)
                rendered_lines.append((shadow, message))
            
            self._message_cache[key] = rendered_lines
        
        return self._message_cache[key]
    
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                # Check if mouse is in the resize handle area (bottom-right corner)
                resize_rect = pygame.Rect(
                    self.rect.right - self.resize_handle_size,
                    self.rect.bottom - self.resize_handle_size,
                    self.resize_handle_size,
                    self.resize_handle_size
                )
                if resize_rect.collidepoint(mouse_pos):
                    self.is_resizing = True
                    self.resize_offset = (
                        self.rect.width - (mouse_pos[0] - self.rect.x),
                        self.rect.height - (mouse_pos[1] - self.rect.y)
                    )
                    return True  # Consume the event
                elif self.rect.collidepoint(mouse_pos):
                    # Check if clicking title bar
                    title_bar = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 30)
                    if title_bar.collidepoint(mouse_pos):
                        self.is_dragging = True
                        self.drag_offset = (self.rect.x - mouse_pos[0], self.rect.y - mouse_pos[1])
                        return True  # Consume the event
            elif event.button == 4:  # Mouse wheel up
                if self.rect.collidepoint(event.pos):
                    self.scroll_offset = min(0, self.scroll_offset + 20)
                    return True  # Consume the event
            elif event.button == 5:  # Mouse wheel down
                if self.rect.collidepoint(event.pos):
                    total_height = sum(self.font.get_height() + self.LINE_SPACING for _ in self.messages)
                    if total_height > self.rect.height - 35:
                        self.scroll_offset = max(-(total_height - self.rect.height + 35),
                                              self.scroll_offset - 20)
                        return True  # Consume the event
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                was_dragging = self.is_dragging
                was_resizing = self.is_resizing
                self.is_dragging = False
                self.is_resizing = False
                return was_dragging or was_resizing  # Consume the event if we were dragging or resizing
        
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                mouse_pos = event.pos
                self.rect.x = mouse_pos[0] + self.drag_offset[0]
                self.rect.y = mouse_pos[1] + self.drag_offset[1]
                
                # Keep within screen bounds
                screen = pygame.display.get_surface()
                self.rect.clamp_ip(screen.get_rect())
                return True  # Consume the event
                
            elif self.is_resizing:
                mouse_pos = event.pos
                new_width = max(self.MIN_WIDTH, mouse_pos[0] - self.rect.x + self.resize_offset[0])
                new_height = max(self.MIN_HEIGHT, mouse_pos[1] - self.rect.y + self.resize_offset[1])
                
                # Update dimensions
                self.rect.width = new_width
                self.rect.height = new_height
                
                # Update surfaces
                self.log_surface = pygame.Surface((new_width, new_height), pygame.SRCALPHA)
                self._update_background()
                
                # Update resize handle position
                self.resize_handle_rect.topleft = (
                    self.rect.width - self.resize_handle_size,
                    self.rect.height - self.resize_handle_size
                )
                return True  # Consume the event
        
        return False
    
    def draw(self, screen: pygame.Surface):
        # Clear message surface
        self.log_surface.fill((0, 0, 0, 0))
        
        # Calculate available width for text
        available_width = self.rect.width - (self.TEXT_PADDING * 2)
        
        # Draw messages
        current_y = 35 + self.scroll_offset  # Start lower after title bar
        
        for text, color in self.messages:
            # Get wrapped and cached message surfaces
            rendered_lines = self._get_cached_message(text, color, available_width)
            
            for shadow_surface, message_surface in rendered_lines:
                # Skip if line would be in title bar area
                if current_y < 30:
                    current_y += self.font.get_height() + self.LINE_SPACING
                    continue
                    
                # Skip if line would be below visible area
                if current_y > self.rect.height:
                    break
                
                # Draw text shadow and message
                self.log_surface.blit(shadow_surface, (self.TEXT_PADDING + 1, current_y + 1))
                self.log_surface.blit(message_surface, (self.TEXT_PADDING, current_y))
                
                current_y += self.font.get_height() + self.LINE_SPACING
        
        # Set up clipping to prevent drawing outside message area
        visible_area = pygame.Rect(0, 30, self.rect.width, self.rect.height - 30)
        self.log_surface.set_clip(visible_area)
        
        # Draw background and messages
        screen.blit(self.background, self.rect)
        screen.blit(self.log_surface, self.rect)
        
        # Reset clipping
        self.log_surface.set_clip(None)
        
        # Draw title with shadow (always on top)
        screen.blit(self.title_shadow, (self.rect.x + 11, self.rect.y + 6))
        screen.blit(self.title_surface, (self.rect.x + 10, self.rect.y + 5))
        
        # Update resize handle rect position for next frame
        self.resize_handle_rect.topleft = (
            self.rect.right - self.resize_handle_size,
            self.rect.bottom - self.resize_handle_size
        ) 