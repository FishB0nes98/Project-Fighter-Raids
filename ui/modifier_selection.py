import pygame
from typing import List, Optional, Callable
from modifiers.modifier_base import Modifier
from ui.button import Button

class ModifierSelectionWindow:
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        self.modifiers: List[Modifier] = []
        self.on_select: Optional[Callable[[Modifier], None]] = None
        self.on_continue: Optional[Callable[[], None]] = None
        self.on_restart: Optional[Callable[[], None]] = None
        self.on_reroll: Optional[Callable[[], None]] = None
        self.has_saved_modifiers = False
        
        # Colors
        self.BG_COLOR = (32, 36, 44)  # Darker background
        self.BORDER_COLOR = (80, 84, 96)
        self.INNER_BORDER_COLOR = (64, 68, 76)
        self.TEXT_COLOR = (220, 220, 220)
        self.TITLE_COLOR = (255, 255, 255)
        self.HOVER_COLOR = (48, 52, 64)
        self.SHADOW_COLOR = (0, 0, 0, 60)
        
        # Font
        self.title_font = pygame.font.Font(None, 56)  # Larger title
        self.text_font = pygame.font.Font(None, 36)
        self.desc_font = pygame.font.Font(None, 32)  # Slightly smaller for descriptions
        
        # Window dimensions
        self.window_width = 1200  # Wider window
        self.window_height = 800  # Taller window
        self.window_x = (screen_width - self.window_width) // 2
        self.window_y = (screen_height - self.window_height) // 2
        
        # Card dimensions
        self.card_width = 320  # Wider cards
        self.card_height = 500  # Taller cards
        self.card_spacing = 60  # More spacing between cards
        
        # Calculate positions for three cards
        total_width = (self.card_width * 3) + (self.card_spacing * 2)
        start_x = (self.window_width - total_width) // 2
        self.card_positions = [
            (start_x + i * (self.card_width + self.card_spacing), 200)
            for i in range(3)
        ]
        
        # Button dimensions
        self.button_width = 200
        self.button_height = 50
        self.button_spacing = 40
        
        # Calculate button positions
        total_button_width = (self.button_width * 2) + self.button_spacing
        button_start_x = (self.window_width - total_button_width) // 2
        self.continue_button_rect = pygame.Rect(button_start_x, 300, self.button_width, self.button_height)
        self.restart_button_rect = pygame.Rect(button_start_x + self.button_width + self.button_spacing, 300, self.button_width, self.button_height)
        
        # Create reroll button
        reroll_y = self.card_positions[0][1] + self.card_height + 30  # Position below cards
        self.reroll_button = Button(
            x=(self.window_width - self.button_width) // 2,
            y=reroll_y,
            width=self.button_width,
            height=self.button_height,
            text="Reroll Modifiers"
        )
        
        self.hovered_card = None
        self.hovered_button = None

    def show(self, modifiers: List[Modifier], on_select: Callable[[Modifier], None], on_continue: Callable[[], None], on_restart: Callable[[], None], on_reroll: Callable[[], None], has_saved_modifiers: bool = False):
        self.modifiers = modifiers
        self.on_select = on_select
        self.on_continue = on_continue
        self.on_restart = on_restart
        self.on_reroll = on_reroll
        self.has_saved_modifiers = has_saved_modifiers
        self.visible = True
        self.hovered_card = None
        self.hovered_button = None

    def hide(self):
        self.visible = False
        self.modifiers = []
        self.on_select = None
        self.on_continue = None
        self.on_restart = None
        self.on_reroll = None
        self.has_saved_modifiers = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            # Adjust mouse position for window position
            relative_pos = (mouse_pos[0] - self.window_x, mouse_pos[1] - self.window_y)
            
            if self.has_saved_modifiers:
                # Check button clicks
                if self.continue_button_rect.collidepoint(relative_pos):
                    if self.on_continue:
                        self.on_continue()
                        self.hide()
                        return True
                elif self.restart_button_rect.collidepoint(relative_pos):
                    if self.on_restart:
                        self.on_restart()
                        self.hide()
                        return True
            else:
                # Check reroll button click
                reroll_relative_pos = (mouse_pos[0] - self.window_x, mouse_pos[1] - self.window_y)
                if self.reroll_button.rect.collidepoint(reroll_relative_pos):
                    if self.on_reroll:
                        self.on_reroll()
                        return True
                
                # Check card clicks
                for i, (x, y) in enumerate(self.card_positions):
                    if i < len(self.modifiers):
                        card_rect = pygame.Rect(x, y, self.card_width, self.card_height)
                        if card_rect.collidepoint(relative_pos):
                            if self.on_select:
                                self.on_select(self.modifiers[i])
                                self.hide()
                                return True

        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            relative_pos = (mouse_pos[0] - self.window_x, mouse_pos[1] - self.window_y)
            
            if self.has_saved_modifiers:
                # Check button hover
                if self.continue_button_rect.collidepoint(relative_pos):
                    self.hovered_button = "continue"
                elif self.restart_button_rect.collidepoint(relative_pos):
                    self.hovered_button = "restart"
                else:
                    self.hovered_button = None
            else:
                # Check reroll button hover
                self.reroll_button.handle_event(pygame.event.Event(
                    pygame.MOUSEMOTION,
                    {'pos': relative_pos}
                ))
                
                # Check card hover
                self.hovered_card = None
                for i, (x, y) in enumerate(self.card_positions):
                    if i < len(self.modifiers):
                        card_rect = pygame.Rect(x, y, self.card_width, self.card_height)
                        if card_rect.collidepoint(relative_pos):
                            self.hovered_card = i
                            break

        return False

    def draw(self, screen: pygame.Surface):
        if not self.visible:
            return

        # Create window surface with alpha for transparency
        window_surface = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        
        # Draw semi-transparent dark overlay on the entire screen
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Dark semi-transparent overlay
        screen.blit(overlay, (0, 0))
        
        # Draw main window background with gradient effect
        background = pygame.Surface((self.window_width, self.window_height))
        background.fill(self.BG_COLOR)
        window_surface.blit(background, (0, 0))
        
        # Draw window border with gradient effect
        pygame.draw.rect(window_surface, self.BORDER_COLOR, 
                        (0, 0, self.window_width, self.window_height), 4, border_radius=15)
        pygame.draw.rect(window_surface, self.INNER_BORDER_COLOR,
                        (4, 4, self.window_width-8, self.window_height-8), 2, border_radius=13)
        
        # Draw title with shadow
        title = "Choose Your Talent" if not self.has_saved_modifiers else "Continue with Saved Modifiers?"
        title_shadow = self.title_font.render(title, True, (0, 0, 0))
        title_surface = self.title_font.render(title, True, self.TITLE_COLOR)
        
        # Add glow effect to title
        glow_surface = pygame.Surface((title_surface.get_width() + 20, title_surface.get_height() + 20), pygame.SRCALPHA)
        glow_color = (*[int(c * 0.5) for c in self.TITLE_COLOR[:3]], 50)
        pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect(), border_radius=10)
        
        title_rect = title_surface.get_rect(centerx=self.window_width//2, y=50)
        window_surface.blit(glow_surface, (title_rect.x - 10, title_rect.y - 10))
        window_surface.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
        window_surface.blit(title_surface, title_rect)

        if self.has_saved_modifiers:
            # Draw continue button
            button_color = self.HOVER_COLOR if self.hovered_button == "continue" else self.BG_COLOR
            pygame.draw.rect(window_surface, button_color, self.continue_button_rect, border_radius=10)
            pygame.draw.rect(window_surface, self.BORDER_COLOR, self.continue_button_rect, 2, border_radius=10)
            
            continue_text = self.text_font.render("Continue", True, self.TEXT_COLOR)
            text_rect = continue_text.get_rect(center=self.continue_button_rect.center)
            window_surface.blit(continue_text, text_rect)
            
            # Draw restart button
            button_color = self.HOVER_COLOR if self.hovered_button == "restart" else self.BG_COLOR
            pygame.draw.rect(window_surface, button_color, self.restart_button_rect, border_radius=10)
            pygame.draw.rect(window_surface, self.BORDER_COLOR, self.restart_button_rect, 2, border_radius=10)
            
            restart_text = self.text_font.render("Restart", True, self.TEXT_COLOR)
            text_rect = restart_text.get_rect(center=self.restart_button_rect.center)
            window_surface.blit(restart_text, text_rect)
        else:
            # Draw modifier cards
            for i, (x, y) in enumerate(self.card_positions):
                if i < len(self.modifiers):
                    modifier = self.modifiers[i]
                    
                    # Card shadow
                    shadow_rect = pygame.Rect(x + 4, y + 4, self.card_width, self.card_height)
                    pygame.draw.rect(window_surface, self.SHADOW_COLOR, shadow_rect, border_radius=10)
                    
                    # Card background
                    card_color = self.HOVER_COLOR if i == self.hovered_card else self.BG_COLOR
                    pygame.draw.rect(window_surface, card_color, 
                                   (x, y, self.card_width, self.card_height), border_radius=10)
                    
                    # Card border with rarity color
                    pygame.draw.rect(window_surface, modifier.rarity.value, 
                                   (x, y, self.card_width, self.card_height), 3, border_radius=10)
                    
                    # Inner border for depth effect
                    pygame.draw.rect(window_surface, self.INNER_BORDER_COLOR,
                                   (x + 3, y + 3, self.card_width - 6, self.card_height - 6), 1, border_radius=8)

                    # Draw rarity label
                    rarity_text = modifier.rarity.name.title()
                    rarity_surface = self.text_font.render(rarity_text, True, modifier.rarity.value)
                    rarity_rect = rarity_surface.get_rect(centerx=x + self.card_width//2, y=y + 20)
                    window_surface.blit(rarity_surface, rarity_rect)
                    
                    # Draw modifier name with shadow
                    name_shadow = self.text_font.render(modifier.name, True, (0, 0, 0))
                    name_surface = self.text_font.render(modifier.name, True, self.TEXT_COLOR)
                    name_rect = name_surface.get_rect(centerx=x + self.card_width//2, y=y + 60)
                    window_surface.blit(name_shadow, (name_rect.x + 1, name_rect.y + 1))
                    window_surface.blit(name_surface, name_rect)
                    
                    # Draw modifier image if available
                    image_y = y + 120  # Move image up a bit
                    if modifier.image_path:
                        try:
                            image = pygame.image.load(modifier.image_path)
                            image = pygame.transform.scale(image, (200, 200))  # Larger image
                            image_rect = image.get_rect(centerx=x + self.card_width//2, y=image_y)
                            window_surface.blit(image, image_rect)
                        except:
                            # Draw colored rectangle if image loading fails
                            color = modifier.rarity.value
                            rect = pygame.Rect(x + 60, image_y, 200, 200)
                            pygame.draw.rect(window_surface, color, rect, border_radius=10)
                    else:
                        # Draw colored rectangle if no image path
                        color = modifier.rarity.value
                        rect = pygame.Rect(x + 60, image_y, 200, 200)
                        pygame.draw.rect(window_surface, color, rect, border_radius=10)

                    # Draw description (word wrapped) below the image
                    desc_start_y = image_y + 220  # Start description below image
                    words = modifier.description.split()
                    lines = []
                    current_line = []
                    for word in words:
                        test_line = ' '.join(current_line + [word])
                        test_surface = self.desc_font.render(test_line, True, self.TEXT_COLOR)
                        if test_surface.get_width() <= self.card_width - 40:  # More padding
                            current_line.append(word)
                        else:
                            if current_line:  # Only add line if it's not empty
                                lines.append(' '.join(current_line))
                                current_line = [word]
                            else:  # Word is too long by itself
                                lines.append(word)
                                current_line = []
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    # Draw description lines with shadow
                    for j, line in enumerate(lines):
                        desc_shadow = self.desc_font.render(line, True, (0, 0, 0))
                        desc_surface = self.desc_font.render(line, True, self.TEXT_COLOR)
                        desc_rect = desc_surface.get_rect(
                            centerx=x + self.card_width//2,
                            y=desc_start_y + j * 35  # More spacing between lines
                        )
                        window_surface.blit(desc_shadow, (desc_rect.x + 1, desc_rect.y + 1))
                        window_surface.blit(desc_surface, desc_rect)
            
            # Draw reroll button
            self.reroll_button.draw(window_surface)

        # Draw the window
        screen.blit(window_surface, (self.window_x, self.window_y)) 