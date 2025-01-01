import pygame
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class ProjectileEffect:
    start_pos: Tuple[float, float]
    end_pos: Tuple[float, float]
    duration: float  # Total time for projectile to reach target
    current_time: float = 0.0  # Current time of animation
    color: Tuple[int, int, int] = (255, 215, 0)  # Default to golden color
    trail_length: int = 5  # Number of trail particles
    size: int = 8  # Size of the projectile
    trail_fade: float = 0.7  # How quickly the trail fades (0-1)
    
    def update(self, dt: float) -> bool:
        """Update the projectile position. Returns True if effect is still active."""
        self.current_time += dt
        return self.current_time < self.duration
    
    def get_current_pos(self) -> Tuple[float, float]:
        """Get the current position of the projectile."""
        progress = min(1.0, self.current_time / self.duration)
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * progress
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * progress
        return (x, y)
    
    def draw(self, screen: pygame.Surface):
        """Draw the projectile and its trail."""
        current_pos = self.get_current_pos()
        
        # Draw trail
        for i in range(self.trail_length):
            # Calculate trail position (going backwards from current position)
            trail_progress = max(0.0, (self.current_time - (i * 0.016)) / self.duration)
            trail_x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * trail_progress
            trail_y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * trail_progress
            
            # Calculate trail alpha and size
            trail_alpha = int(255 * (1 - (i / self.trail_length)) * self.trail_fade)
            trail_size = max(2, self.size - i)
            
            # Draw trail particle with glow
            glow_size = trail_size * 3  # Increased glow size
            glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            glow_color = (*self.color, trail_alpha // 2)  # Made glow more visible
            pygame.draw.circle(glow_surface, glow_color, (glow_size, glow_size), glow_size)
            screen.blit(glow_surface, (trail_x - glow_size, trail_y - glow_size))
            
            # Draw main trail particle
            trail_surface = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
            trail_color = (*self.color, trail_alpha)
            pygame.draw.circle(trail_surface, trail_color, (trail_size, trail_size), trail_size)
            
            # Add white core to trail
            core_size = max(1, trail_size // 2)
            pygame.draw.circle(trail_surface, (255, 255, 255, trail_alpha), (trail_size, trail_size), core_size)
            screen.blit(trail_surface, (trail_x - trail_size, trail_y - trail_size))
        
        # Draw main projectile with enhanced glow
        glow_size = self.size * 3  # Increased glow size
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        
        # Draw multiple layers of glow for more intensity
        pygame.draw.circle(glow_surface, (*self.color, 60), (glow_size, glow_size), glow_size)
        pygame.draw.circle(glow_surface, (*self.color, 90), (glow_size, glow_size), glow_size * 0.7)
        pygame.draw.circle(glow_surface, (*self.color, 120), (glow_size, glow_size), glow_size * 0.5)
        screen.blit(glow_surface, (current_pos[0] - glow_size, current_pos[1] - glow_size))
        
        # Draw main projectile with white core
        projectile_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(projectile_surface, (*self.color, 255), (self.size, self.size), self.size)
        pygame.draw.circle(projectile_surface, (255, 255, 255, 255), (self.size, self.size), self.size * 0.5)  # White core
        screen.blit(projectile_surface, (current_pos[0] - self.size, current_pos[1] - self.size))

class VisualEffectManager:
    def __init__(self):
        self.active_effects: List[ProjectileEffect] = []
    
    def add_effect(self, effect):
        self.active_effects.append(effect)
        print(f"Added new effect, total effects: {len(self.active_effects)}")  # Debug print
    
    def update(self, dt: float):
        """Update all active effects and remove completed ones."""
        initial_count = len(self.active_effects)  # Debug count
        self.active_effects = [effect for effect in self.active_effects if effect.update(dt)]
        final_count = len(self.active_effects)  # Debug count
        if initial_count != final_count:
            print(f"Updated effects: {initial_count} -> {final_count}")  # Debug print
    
    def draw(self, screen: pygame.Surface):
        """Draw all active effects."""
        if self.active_effects:  # Debug print
            print(f"Drawing {len(self.active_effects)} effects")
        for effect in self.active_effects:
            effect.draw(screen)
    
    def create_projectile(self, start_pos: Tuple[float, float], end_pos: Tuple[float, float], 
                         color: Tuple[int, int, int] = (255, 215, 0), duration: float = 0.5,
                         size: int = 8, trail_length: int = 5) -> ProjectileEffect:
        """Helper method to create a projectile effect."""
        return ProjectileEffect(
            start_pos=start_pos,
            end_pos=end_pos,
            color=color,
            duration=duration,
            size=size,
            trail_length=trail_length
        ) 