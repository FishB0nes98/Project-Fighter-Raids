import pygame
import os
import random
import math
from pathlib import Path

def create_kick_icon():
    """Create icon for Kick ability"""
    surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    
    # Draw leg shape
    leg_color = (220, 180, 140)  # Skin tone
    boot_color = (139, 69, 19)   # Brown boot
    
    # Boot
    pygame.draw.polygon(surface, boot_color, [
        (40, 45),  # Top right
        (45, 50),  # Bottom right
        (35, 55),  # Bottom
        (25, 50),  # Bottom left
        (30, 45)   # Top left
    ])
    
    # Leg
    pygame.draw.polygon(surface, leg_color, [
        (35, 15),  # Top
        (40, 20),  # Right
        (40, 45),  # Bottom right
        (30, 45),  # Bottom left
        (30, 20)   # Left
    ])
    
    # Add motion lines
    for i in range(3):
        start_pos = (45 + i * 5, 35 + i * 5)
        end_pos = (55 + i * 5, 45 + i * 5)
        pygame.draw.line(surface, (255, 255, 255, 150), start_pos, end_pos, 2)
    
    return surface

def create_slam_icon():
    """Create icon for Slam ability"""
    surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    
    # Draw fist shape
    fist_color = (220, 180, 140)  # Skin tone
    
    # Main fist
    pygame.draw.circle(surface, fist_color, (32, 32), 15)
    
    # Add impact lines radiating from center
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        start_x = 32 + math.cos(rad) * 20
        start_y = 32 + math.sin(rad) * 20
        end_x = 32 + math.cos(rad) * 30
        end_y = 32 + math.sin(rad) * 30
        pygame.draw.line(surface, (255, 50, 50, 200), (start_x, start_y), (end_x, end_y), 3)
    
    # Add shockwave circles
    for radius in [25, 28, 31]:
        pygame.draw.circle(surface, (255, 50, 50, 100), (32, 32), radius, 2)
    
    return surface

def generate_all_icons():
    """Generate all ability icons and save them"""
    pygame.init()
    
    # Create abilities directory if it doesn't exist
    ability_path = Path("assets/abilities")
    ability_path.mkdir(parents=True, exist_ok=True)
    
    # Generate and save each icon
    icons = {
        "kick.png": create_kick_icon(),
        "slam.png": create_slam_icon()
    }
    
    for filename, surface in icons.items():
        pygame.image.save(surface, str(ability_path / filename))
        print(f"Generated {filename}")
    
    pygame.quit()

if __name__ == "__main__":
    generate_all_icons() 