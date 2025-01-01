from typing import List, Dict, Optional
from characters.base_character import Character
from stages.base_stage import BaseStage
from stages.stage_3 import Stage3
from ui.button import Button
import pygame

class StageManager:
    def __init__(self):
        self.stages: Dict[int, BaseStage] = {}
        self.current_stage: Optional[BaseStage] = None
        self.player_characters: List[Character] = []
        
        # End turn button properties
        self.end_turn_button_pos = (1700, 900)  # Position near bottom-right
        self.END_TURN_BG_COLOR = (48, 52, 64)
        self.END_TURN_BORDER_COLOR = (80, 84, 96)
        self.END_TURN_TEXT_COLOR = (220, 220, 220)
        self.END_TURN_HOVER_COLOR = (64, 68, 80)
        self.end_turn_font = pygame.font.Font(None, 36)
        self.is_end_turn_hovered = False
    
    @property
    def current_stage_number(self) -> Optional[int]:
        """Get the current stage number."""
        return self.current_stage.stage_number if self.current_stage else None
    
    def add_stage(self, stage: BaseStage):
        self.stages[stage.stage_number] = stage
    
    def set_player_characters(self, characters: List[Character]):
        self.player_characters = characters
    
    def start_stage(self, stage_number: int) -> bool:
        if stage_number not in self.stages:
            return False
        
        if self.current_stage:
            self.current_stage.on_exit()
        
        self.current_stage = self.stages[stage_number]
        self.current_stage.initialize()
        self.current_stage.on_enter()
        return True
    
    def is_battle_won(self) -> bool:
        if not self.current_stage:
            return False
        return self.current_stage.is_completed()
    
    def is_battle_lost(self) -> bool:
        return all(not char.is_alive() for char in self.player_characters)
    
    def update(self):
        # Update all characters
        for character in self.player_characters:
            character.update()
        
        if self.current_stage:
            self.current_stage.update()
    
    def handle_events(self, event) -> bool:
        """Handle events for the stage manager. Returns True if end turn button was clicked."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if end turn button was clicked
            button_rect = pygame.Rect(self.end_turn_button_pos, (200, 50))
            if button_rect.collidepoint(event.pos):
                return True
        elif event.type == pygame.MOUSEMOTION:
            # Update hover state
            button_rect = pygame.Rect(self.end_turn_button_pos, (200, 50))
            self.is_end_turn_hovered = button_rect.collidepoint(event.pos)
        return False
    
    def can_end_turn(self) -> bool:
        """Check if turn can be ended (no available actions)"""
        if not self.current_stage:
            return False
            
        # For player turn, check if any character has available abilities with enough mana
        for char in self.player_characters:
            for ability in char.abilities:
                if ability.can_use(char):
                    return False
        return True
    
    def draw(self, screen: pygame.Surface):
        if self.current_stage:
            # Draw stage (includes background and bosses)
            self.current_stage.draw(screen)
            
            # Only position characters if not in Stage 3
            if not isinstance(self.current_stage, Stage3):
                # Draw player characters
                char_spacing = 1920 // (len(self.player_characters) + 1)
                for i, char in enumerate(self.player_characters, 1):
                    char.position = (char_spacing * i - char.image.get_width() // 2, 600)
                    char.draw(screen)
            else:
                # For Stage 3, just draw the characters at their current positions
                for char in self.player_characters:
                    char.draw(screen)
        
        # Draw end turn button
        button_rect = pygame.Rect(self.end_turn_button_pos, (200, 50))
        
        # Draw border
        border_rect = button_rect.inflate(4, 4)
        pygame.draw.rect(screen, self.END_TURN_BORDER_COLOR, border_rect, border_radius=8)
        
        # Draw background with hover effect
        bg_color = self.END_TURN_HOVER_COLOR if self.is_end_turn_hovered else self.END_TURN_BG_COLOR
        pygame.draw.rect(screen, bg_color, button_rect, border_radius=6)
        
        # Draw text with shadow
        text = "End Turn"
        shadow_surface = self.end_turn_font.render(text, True, (0, 0, 0))
        text_surface = self.end_turn_font.render(text, True, self.END_TURN_TEXT_COLOR)
        
        # Center text in button
        shadow_rect = shadow_surface.get_rect(center=(button_rect.centerx + 2, button_rect.centery + 2))
        text_rect = text_surface.get_rect(center=button_rect.center)
        
        # Draw shadow and text
        screen.blit(shadow_surface, shadow_rect)
        screen.blit(text_surface, text_rect) 