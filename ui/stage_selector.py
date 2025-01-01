import pygame
from typing import Dict, Optional, Callable, Tuple
from stages.base_stage import BaseStage
import math
from PIL import Image

class StageSelector:
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        self.stages: Dict[int, BaseStage] = {}
        self.on_select: Optional[Callable[[int], None]] = None
        
        # Cache for scaled images
        self.preview_cache: Dict[Tuple[int, int, int], pygame.Surface] = {}
        self.star_cache: Dict[Tuple[int, float], pygame.Surface] = {}
        self.text_cache: Dict[Tuple[str, int, Tuple[int, int, int]], pygame.Surface] = {}  # Cache for rendered text
        
        # Constants for scaling
        self.NORMAL_SCALE = 1.0
        self.HOVER_SCALE = 1.05
        
        # Modern color palette with transparency
        self.BG_COLOR = (12, 12, 18)  # Darker background
        self.CARD_BG = (28, 28, 36)  # Card background
        self.CARD_BG_ALPHA = 240  # Separate alpha value
        self.CARD_HOVER_BG = (38, 38, 46)  # Lighter when hovered
        self.CARD_HOVER_BG_ALPHA = 240  # Separate alpha value
        self.BORDER_COLOR = (64, 68, 76)  # Brighter border
        self.TEXT_COLOR = (255, 255, 255)
        self.SUBTITLE_COLOR = (200, 200, 210)  # Brighter subtitle
        self.DESC_COLOR = (180, 180, 190)  # Slightly dimmer for descriptions
        self.STAR_COLOR = (255, 225, 125)  # Brighter gold for stars
        self.STAR_OUTLINE = (255, 235, 140)  # Brighter outline
        self.STAR_GLOW = (255, 225, 125)  # Star glow color
        self.STAR_GLOW_ALPHA = 30  # Separate alpha for glow
        self.STAR_BG_COLOR = (45, 45, 55)  # Darker for empty stars
        
        # Stage difficulties (in stars)
        self.STAGE_DIFFICULTIES = {
            1: 1.0,  # Stage 1: 1 star
            2: 1.5,  # Stage 2: 1.5 stars
            3: 1.5,  # Stage 3: 1.5 stars
            4: 2.5,  # Stage 4: 2.5 stars
            5: 4.0,  # Stage 5: 4 stars
        }
        
        # Load fonts (using default for now, but you should use custom fonts)
        self.title_font = pygame.font.Font(None, 72)  # Larger title
        self.stage_title_font = pygame.font.Font(None, 42)  # Larger stage titles
        self.desc_font = pygame.font.Font(None, 28)  # Slightly larger descriptions
        self.difficulty_font = pygame.font.Font(None, 24)
        
        # Grid layout settings - wider cards with more spacing
        self.cards_per_row = 3
        self.card_width = 380  # Wider cards
        self.card_height = 480  # Taller cards
        self.card_spacing = 40  # More spacing
        self.vertical_spacing = 60  # More vertical spacing
        
        # Scroll settings with smoother animation
        self.scroll_offset = 0
        self.target_scroll = 0
        self.scroll_speed = 0.3  # Faster scroll
        self.max_scroll = 0
        
        # Animation variables with smoother transitions
        self.hover_scales = {stage_num: 1.0 for stage_num in range(1, 8)}
        self.target_scales = {stage_num: 1.0 for stage_num in range(1, 8)}
        self.hovered_stage = None
        self.animation_speed = 0.25  # Smoother animations
        
        # Hover effect variables
        self.hover_glow = 0
        self.glow_direction = 1
        self.glow_speed = 0.08  # Slower glow for smoother effect
        
        # Calculate positions
        self.calculate_positions()
        
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
        
    def calculate_positions(self):
        """Calculate grid positions for stage cards"""
        self.card_positions = {}
        total_rows = math.ceil(len(self.stages) / self.cards_per_row)
        
        content_width = (self.card_width * self.cards_per_row) + (self.card_spacing * (self.cards_per_row - 1))
        start_x = (self.screen_width - content_width) // 2
        start_y = 150  # Space for title
        
        for stage_num in sorted(self.stages.keys()):
            idx = stage_num - 1
            row = idx // self.cards_per_row
            col = idx % self.cards_per_row
            
            x = start_x + col * (self.card_width + self.card_spacing)
            y = start_y + row * (self.card_height + self.vertical_spacing)
            
            self.card_positions[stage_num] = (x, y)
        
        # Calculate max scroll
        total_height = start_y + (total_rows * (self.card_height + self.vertical_spacing))
        self.max_scroll = max(0, total_height - (self.screen_height - 100))
    
    def show(self, stages: Dict[int, BaseStage], on_select: Callable[[int], None]):
        self.stages = stages
        self.on_select = on_select
        self.visible = True
        self.scroll_offset = 0
        self.target_scroll = 0
        self.preview_cache.clear()
        self.text_cache.clear()  # Clear text cache when showing new stages
        self.calculate_positions()
        
        # Pre-cache all stage previews and text
        for stage_num, stage in stages.items():
            # Pre-cache previews
            normal_preview_height = int(self.card_height * 0.55)
            normal_preview_width = self.card_width - 40
            hover_preview_height = int(self.card_height * self.HOVER_SCALE * 0.55)
            hover_preview_width = int(self.card_width * self.HOVER_SCALE - 40)
            
            self.get_cached_preview(stage.background, normal_preview_width, normal_preview_height)
            self.get_cached_preview(stage.background, hover_preview_width, hover_preview_height)
            
            # Pre-cache text
            self.text_cache[(f"Stage {stage_num}", 1, self.TEXT_COLOR)] = self.stage_title_font.render(f"Stage {stage_num}", True, self.TEXT_COLOR)
            self.text_cache[(stage.name, 2, self.SUBTITLE_COLOR)] = self.stage_title_font.render(stage.name, True, self.SUBTITLE_COLOR)
            
            # Pre-cache description words
            for word in stage.description.split():
                word_key = (word + " ", 3, self.DESC_COLOR)
                if word_key not in self.text_cache:
                    self.text_cache[word_key] = self.desc_font.render(word + " ", True, self.DESC_COLOR)
    
    def hide(self):
        self.visible = False
        self.stages = {}
        self.on_select = None
        self.preview_cache.clear()
        self.star_cache.clear()
        self.text_cache.clear()  # Clear text cache when hiding
    
    def get_cached_preview(self, stage_background: pygame.Surface, width: int, height: int) -> pygame.Surface:
        """Get a cached preview image or create and cache a new one."""
        cache_key = (id(stage_background), width, height)
        
        if cache_key not in self.preview_cache:
            # Create new scaled preview
            self.preview_cache[cache_key] = self.high_quality_scale(stage_background, (width, height))
        
        return self.preview_cache[cache_key]
    
    def update(self):
        if not self.visible:
            return
        
        # Update hover glow effect
        self.hover_glow += self.glow_speed * self.glow_direction
        if self.hover_glow >= 1.0:
            self.hover_glow = 1.0
            self.glow_direction = -1
        elif self.hover_glow <= 0.0:
            self.hover_glow = 0.0
            self.glow_direction = 1
        
        # Update hover scale animations
        for stage_num in self.stages:
            if self.hover_scales[stage_num] != self.target_scales[stage_num]:
                diff = self.target_scales[stage_num] - self.hover_scales[stage_num]
                self.hover_scales[stage_num] += diff * self.animation_speed
        
        # Update smooth scrolling
        if self.scroll_offset != self.target_scroll:
            diff = self.target_scroll - self.scroll_offset
            self.scroll_offset += diff * self.scroll_speed
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in (4, 5):  # Mouse wheel
                scroll_amount = 50 if event.button == 4 else -50
                self.target_scroll = max(0, min(self.max_scroll, self.target_scroll - scroll_amount))
                return False
            
            mouse_pos = pygame.mouse.get_pos()
            adjusted_pos = (mouse_pos[0], mouse_pos[1] + self.scroll_offset)
            
            for stage_num, pos in self.card_positions.items():
                rect = pygame.Rect(pos[0], pos[1] - self.scroll_offset, self.card_width, self.card_height)
                if rect.collidepoint(mouse_pos):
                    if self.on_select:
                        self.on_select(stage_num)
                        return True
        
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            adjusted_pos = (mouse_pos[0], mouse_pos[1] + self.scroll_offset)
            hover_found = False
            
            for stage_num, pos in self.card_positions.items():
                rect = pygame.Rect(pos[0], pos[1] - self.scroll_offset, self.card_width, self.card_height)
                if rect.collidepoint(mouse_pos):
                    self.hovered_stage = stage_num
                    self.target_scales[stage_num] = 1.05
                    hover_found = True
                else:
                    self.target_scales[stage_num] = 1.0
            
            if not hover_found:
                self.hovered_stage = None
        
        return False
    
    def draw_star(self, screen: pygame.Surface, x: int, y: int, fill: float = 1.0, size: int = 12):
        """Draw a traditional 5-point star with high quality scaling and caching"""
        # Create cache key based on size and fill amount
        cache_key = (size, fill)
        
        # Check if we have this star cached
        if cache_key not in self.star_cache:
            # Create a larger surface for the star (4x size for better quality)
            large_size = size * 4
            star_surface = pygame.Surface((large_size * 2, large_size * 2), pygame.SRCALPHA)
            
            # Calculate points for larger star
            points = []
            for i in range(5):
                angle = math.pi * (2 * i / 5 - 0.5)
                point_x = large_size + large_size * math.cos(angle)
                point_y = large_size + large_size * math.sin(angle)
                points.append((point_x, point_y))
                
                # Calculate inner points
                inner_angle = math.pi * (2 * i / 5 - 0.5 + 0.2)
                inner_x = large_size + large_size * 0.4 * math.cos(inner_angle)
                inner_y = large_size + large_size * 0.4 * math.sin(inner_angle)
                points.append((inner_x, inner_y))
            
            # Draw base star (empty or background)
            if fill < 1.0:
                pygame.draw.polygon(star_surface, self.STAR_BG_COLOR, points)
            
            if fill > 0:
                # For partial fill, create a clipping rect
                if fill < 1.0:
                    clip_rect = pygame.Rect(0, 0, large_size * 2 * fill, large_size * 2)
                    old_clip = star_surface.get_clip()
                    star_surface.set_clip(clip_rect)
                
                # Draw filled star
                pygame.draw.polygon(star_surface, self.STAR_COLOR, points)
                
                # Reset clip
                if fill < 1.0:
                    star_surface.set_clip(old_clip)
            
            # Scale down the star using high quality scaling
            final_size = (size * 2, size * 2)
            scaled_star = self.high_quality_scale(star_surface, final_size)
            
            # Cache the scaled star
            self.star_cache[cache_key] = scaled_star
        
        # Draw the cached star at the correct position
        screen.blit(self.star_cache[cache_key], (x - size, y - size))

    def draw_difficulty_stars(self, screen: pygame.Surface, x: int, y: int, stage_num: int, max_stars: int = 5):
        """Draw the difficulty rating as stars"""
        difficulty = self.STAGE_DIFFICULTIES.get(stage_num, 0)
        star_spacing = 20  # Increased spacing slightly
        
        # Draw star background
        padding = 15
        bg_width = max_stars * star_spacing + padding * 2
        bg_height = 30
        
        star_bg = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        pygame.draw.rect(star_bg, (*self.CARD_BG, 180), star_bg.get_rect(), border_radius=15)
        screen.blit(star_bg, (x, y))
        
        # Draw stars
        y_offset = bg_height // 2
        for i in range(max_stars):
            star_x = x + padding + (i * star_spacing)
            star_y = y + y_offset
            
            if i < int(difficulty):
                # Full star
                self.draw_star(screen, star_x, star_y, 1.0)
            elif i == int(difficulty) and difficulty % 1 != 0:
                # Partial star
                self.draw_star(screen, star_x, star_y, difficulty % 1)
            else:
                # Empty star
                self.draw_star(screen, star_x, star_y, 0)

    def draw_card(self, screen: pygame.Surface, stage_num: int, stage: BaseStage, pos: Tuple[int, int], scale: float):
        x, y = pos
        y -= self.scroll_offset
        
        # Skip drawing if card is outside visible area
        if y + self.card_height < 0 or y > self.screen_height:
            return
        
        # Calculate scaled dimensions
        scaled_width = int(self.card_width * scale)
        scaled_height = int(self.card_height * scale)
        x = x - (scaled_width - self.card_width) // 2
        y = y - (scaled_height - self.card_height) // 2
        
        # Draw card shadow with larger blur
        for i in range(3):  # Multiple passes for softer shadow
            shadow_surface = pygame.Surface((scaled_width + 20 + i*2, scaled_height + 20 + i*2), pygame.SRCALPHA)
            shadow_color = (0, 0, 0, 20 - i*5)  # Decreasing opacity for each pass
            pygame.draw.rect(shadow_surface, shadow_color, shadow_surface.get_rect(), border_radius=15)
            screen.blit(shadow_surface, (x - 10 - i, y + 5 + i))
        
        # Draw card background with hover effect
        card_rect = pygame.Rect(x, y, scaled_width, scaled_height)
        card_surface = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
        bg_color = (*self.CARD_HOVER_BG, self.CARD_HOVER_BG_ALPHA) if stage_num == self.hovered_stage else (*self.CARD_BG, self.CARD_BG_ALPHA)
        pygame.draw.rect(card_surface, bg_color, card_surface.get_rect(), border_radius=15)
        screen.blit(card_surface, card_rect)
        
        # Draw stage preview using cached high quality scaling
        preview_height = int(scaled_height * 0.55)  # Larger preview
        preview_width = scaled_width - 40
        preview = self.get_cached_preview(stage.background, preview_width, preview_height)
        screen.blit(preview, (x + 20, y + 20))
        
        # Draw difficulty stars with glow effect when hovered
        star_y = y + preview_height + 30
        self.draw_difficulty_stars(screen, x + 20, star_y, stage_num)
        
        # Draw stage info with better text wrapping
        text_y = star_y + 40
        
        # Cache and draw stage title
        title_key = (f"Stage {stage_num}", 1, self.TEXT_COLOR)
        if title_key not in self.text_cache:
            self.text_cache[title_key] = self.stage_title_font.render(f"Stage {stage_num}", True, self.TEXT_COLOR)
        screen.blit(self.text_cache[title_key], (x + 20, text_y))
        
        # Cache and draw stage name
        name_key = (stage.name, 2, self.SUBTITLE_COLOR)
        if name_key not in self.text_cache:
            self.text_cache[name_key] = self.stage_title_font.render(stage.name, True, self.SUBTITLE_COLOR)
        screen.blit(self.text_cache[name_key], (x + 20, text_y + 35))
        
        # Word wrap and cache description
        desc_y = text_y + 85
        max_width = scaled_width - 40
        words = stage.description.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_key = (word + " ", 3, self.DESC_COLOR)
            if word_key not in self.text_cache:
                self.text_cache[word_key] = self.desc_font.render(word + " ", True, self.DESC_COLOR)
            word_surface = self.text_cache[word_key]
            word_width = word_surface.get_width()
            
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
        
        if current_line:
            lines.append(" ".join(current_line))
        
        # Draw description lines with shadow effect
        for i, line in enumerate(lines[:3]):  # Show up to 3 lines
            line_key = (line, 3, self.DESC_COLOR)
            if line_key not in self.text_cache:
                self.text_cache[line_key] = self.desc_font.render(line, True, self.DESC_COLOR)
            line_surface = self.text_cache[line_key]
            screen.blit(line_surface, (x + 20, desc_y + i * 30))
        
        # Draw border with gradient effect
        if stage_num == self.hovered_stage:
            # Draw outer glow
            glow_surface = pygame.Surface((scaled_width + 4, scaled_height + 4), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*self.STAR_GLOW, self.STAR_GLOW_ALPHA), glow_surface.get_rect(), border_radius=15)
            screen.blit(glow_surface, (x - 2, y - 2))
        
        # Draw border
        pygame.draw.rect(screen, self.BORDER_COLOR, card_rect, 2, border_radius=15)
    
    def draw(self, screen: pygame.Surface):
        if not self.visible:
            return
        
        # Draw dark overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.fill(self.BG_COLOR)
        screen.blit(overlay, (0, 0))
        
        # Draw title
        title = "Select Stage"
        title_shadow = self.title_font.render(title, True, (0, 0, 0))
        title_surface = self.title_font.render(title, True, self.TEXT_COLOR)
        
        title_y = 50
        shadow_rect = title_shadow.get_rect(center=(self.screen_width // 2 + 2, title_y + 2))
        text_rect = title_surface.get_rect(center=(self.screen_width // 2, title_y))
        
        screen.blit(title_shadow, shadow_rect)
        screen.blit(title_surface, text_rect)
        
        # Draw stage cards
        for stage_num, stage in sorted(self.stages.items()):
            self.draw_card(screen, stage_num, stage, self.card_positions[stage_num], self.hover_scales[stage_num])
        
        # Draw scroll indicators if needed
        if self.max_scroll > 0:
            if self.scroll_offset > 0:
                # Draw up arrow
                pygame.draw.polygon(screen, self.TEXT_COLOR, [
                    (self.screen_width // 2 - 10, 120),
                    (self.screen_width // 2 + 10, 120),
                    (self.screen_width // 2, 100)
                ])
            
            if self.scroll_offset < self.max_scroll:
                # Draw down arrow
                pygame.draw.polygon(screen, self.TEXT_COLOR, [
                    (self.screen_width // 2 - 10, self.screen_height - 20),
                    (self.screen_width // 2 + 10, self.screen_height - 20),
                    (self.screen_width // 2, self.screen_height - 40)
                ]) 