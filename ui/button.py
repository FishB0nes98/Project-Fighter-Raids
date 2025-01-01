import pygame

class Button:
    # Colors
    BG_COLOR = (48, 52, 64)
    BORDER_COLOR = (80, 84, 96)
    HOVER_COLOR = (60, 64, 76)
    TEXT_COLOR = (220, 220, 220)
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font_size: int = 24):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.is_hovered = False
        
        # Pre-render text
        self.text_surface = self.font.render(text, True, self.TEXT_COLOR)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)
        
        # Shadow text
        self.shadow_surface = self.font.render(text, True, (0, 0, 0))
        self.shadow_rect = self.text_rect.copy()
        self.shadow_rect.x += 1
        self.shadow_rect.y += 1
    
    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False
    
    def draw(self, screen: pygame.Surface):
        # Draw border
        border_rect = self.rect.inflate(4, 4)
        pygame.draw.rect(screen, self.BORDER_COLOR, border_rect, border_radius=8)
        
        # Draw button background
        color = self.HOVER_COLOR if self.is_hovered else self.BG_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        
        # Draw text shadow
        screen.blit(self.shadow_surface, self.shadow_rect)
        # Draw text
        screen.blit(self.text_surface, self.text_rect) 