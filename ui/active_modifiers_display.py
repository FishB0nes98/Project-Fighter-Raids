import pygame
from typing import List
from modifiers.modifier_base import Modifier

class ActiveModifiersDisplay:
    def __init__(self, screen_width: int):
        # Constants
        self.PADDING = 20
        self.ICON_SIZE = 48
        self.SPACING = 10
        self.BG_COLOR = (32, 36, 44, 220)  # Dark background with transparency
        self.BORDER_COLOR = (80, 84, 96)
        self.INNER_BORDER_COLOR = (64, 68, 76)
        self.TEXT_COLOR = (220, 220, 220)
        
        # Position in top-left corner
        self.x = self.PADDING
        self.y = self.PADDING
        
        # Fonts
        self.title_font = pygame.font.Font(None, 32)
        self.desc_font = pygame.font.Font(None, 24)
        
        # Tooltip state
        self.hovered_modifier = None
        
    def draw(self, screen: pygame.Surface, active_modifiers: List[Modifier]):
        if not active_modifiers:
            return
            
        # Calculate total width needed
        total_width = (len(active_modifiers) * (self.ICON_SIZE + self.SPACING)) + self.PADDING * 2
        
        # Create background surface with alpha
        background = pygame.Surface((total_width, self.ICON_SIZE + self.PADDING * 2), pygame.SRCALPHA)
        
        # Draw background with rounded corners
        pygame.draw.rect(background, self.BG_COLOR, 
                        background.get_rect(), border_radius=10)
        
        # Draw borders
        pygame.draw.rect(background, self.BORDER_COLOR, 
                        background.get_rect(), 2, border_radius=10)
        pygame.draw.rect(background, self.INNER_BORDER_COLOR,
                        background.get_rect().inflate(-2, -2), 1, border_radius=9)
        
        # Position for first modifier
        icon_x = self.PADDING
        
        # Get mouse position for hover detection
        mouse_pos = pygame.mouse.get_pos()
        screen_pos = (self.x, self.y)  # Now using top-left position
        
        # Draw each modifier
        for i, modifier in enumerate(active_modifiers):
            icon_pos = (icon_x, self.PADDING)
            
            # Draw modifier icon or colored rectangle
            if modifier.image_path:
                try:
                    image = pygame.image.load(modifier.image_path)
                    image = pygame.transform.scale(image, (self.ICON_SIZE, self.ICON_SIZE))
                    background.blit(image, icon_pos)
                except:
                    # Draw colored rectangle if image fails to load
                    pygame.draw.rect(background, modifier.rarity.value,
                                   pygame.Rect(icon_pos, (self.ICON_SIZE, self.ICON_SIZE)),
                                   border_radius=5)
            else:
                # Draw colored rectangle if no image
                pygame.draw.rect(background, modifier.rarity.value,
                               pygame.Rect(icon_pos, (self.ICON_SIZE, self.ICON_SIZE)),
                               border_radius=5)
            
            # Add glow effect for rarity
            glow_surface = pygame.Surface((self.ICON_SIZE + 4, self.ICON_SIZE + 4), pygame.SRCALPHA)
            glow_color = (*modifier.rarity.value[:3], 100)  # Semi-transparent version of rarity color
            pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect(), border_radius=6)
            background.blit(glow_surface, (icon_pos[0] - 2, icon_pos[1] - 2))
            
            # Check for hover
            hover_rect = pygame.Rect(screen_pos[0] + icon_x, screen_pos[1] + self.PADDING,
                                   self.ICON_SIZE, self.ICON_SIZE)
            if hover_rect.collidepoint(mouse_pos):
                self.hovered_modifier = modifier
            
            icon_x += self.ICON_SIZE + self.SPACING
        
        # Draw the background to the screen
        screen.blit(background, screen_pos)
        
        # Draw tooltip for hovered modifier
        if self.hovered_modifier:
            self._draw_tooltip(screen, mouse_pos, self.hovered_modifier)
            self.hovered_modifier = None  # Reset hover state
    
    def _draw_tooltip(self, screen: pygame.Surface, mouse_pos: tuple, modifier: Modifier):
        # Padding and colors for tooltip
        TOOLTIP_PADDING = 16
        TOOLTIP_BG = (32, 36, 44, 240)
        TOOLTIP_BORDER = (80, 84, 96)
        
        # Create text surfaces
        title = modifier.name
        title_surface = self.title_font.render(title, True, self.TEXT_COLOR)
        
        # Split description into lines
        desc_words = modifier.description.split()
        desc_lines = []
        current_line = []
        
        for word in desc_words:
            test_line = ' '.join(current_line + [word])
            test_surface = self.desc_font.render(test_line, True, self.TEXT_COLOR)
            if test_surface.get_width() <= 300:  # Max tooltip width
                current_line.append(word)
            else:
                if current_line:
                    desc_lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    desc_lines.append(word)
        if current_line:
            desc_lines.append(' '.join(current_line))
        
        desc_surfaces = [self.desc_font.render(line, True, self.TEXT_COLOR) for line in desc_lines]
        
        # Calculate tooltip dimensions
        width = max(title_surface.get_width(),
                   *[s.get_width() for s in desc_surfaces]) + TOOLTIP_PADDING * 2
        height = (TOOLTIP_PADDING * 2 + title_surface.get_height() +
                 sum(s.get_height() + 5 for s in desc_surfaces))
        
        # Position tooltip near mouse but keep on screen
        x = min(mouse_pos[0], screen.get_width() - width - 10)
        y = mouse_pos[1] - height - 10
        if y < 10:  # If tooltip would go off top of screen, show below cursor
            y = mouse_pos[1] + 20
        
        # Create tooltip surface
        tooltip = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw tooltip background and border
        pygame.draw.rect(tooltip, TOOLTIP_BG, tooltip.get_rect(), border_radius=10)
        pygame.draw.rect(tooltip, TOOLTIP_BORDER, tooltip.get_rect(), 2, border_radius=10)
        
        # Draw title
        title_pos = (TOOLTIP_PADDING, TOOLTIP_PADDING)
        tooltip.blit(title_surface, title_pos)
        
        # Draw description
        desc_y = title_pos[1] + title_surface.get_height() + 10
        for surface in desc_surfaces:
            tooltip.blit(surface, (TOOLTIP_PADDING, desc_y))
            desc_y += surface.get_height() + 5
        
        # Draw tooltip to screen
        screen.blit(tooltip, (x, y)) 