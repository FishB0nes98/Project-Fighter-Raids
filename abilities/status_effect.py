import pygame

class StatusEffect:
    def __init__(self, type: str, value: float, duration: int, icon: pygame.Surface):
        self.type = type
        self.value = value
        self.duration = duration
        self.icon = icon
        self.name = ""
        self.description = ""
    
    def update(self) -> bool:
        """Update the status effect and return True if it should continue"""
        self.duration -= 1
        return self.duration > 0
    
    def get_tooltip_title(self) -> str:
        """Return the title to show in the buff tooltip"""
        return self.name
    
    def get_tooltip_text(self) -> str:
        """Return the text to show in the buff tooltip"""
        if self.type == "stealth":
            return self.description
        # For other buff types, show value and duration
        if self.value != 0:
            return f"Increases stats by {self.value}\n{self.duration} turns remaining"
        return self.description 