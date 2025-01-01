from items.base_item import Item
from characters.base_character import Character, StatusEffect
import pygame

class IceBlade(Item):
    def __init__(self):
        super().__init__(
            name="Ice Blade",
            description="A legendary blade forged in the depths of the frozen abyss. Grants permanent 50% damage increase.",
            rarity="Legendary",
            item_type="Buff",
            icon_path="assets/items/ice_blade.png",
            max_stack=1
        )
        self.cooldown = 100  # 100 turns cooldown
    
    def use(self, user: Character, target: Character) -> bool:
        """Apply permanent damage increase buff to the target."""
        # Call base class use method to log the use
        super().use(user, target)
        
        # Create a custom buff that increases damage dealt
        class IceBladeBuff(StatusEffect):
            def __init__(self, icon):
                super().__init__("custom", 50, -1, icon)  # 50% increase, permanent
                self.name = "Ice Blade"
                self.description = "Damage increased by 50%"
            
            def apply_damage_increase(self, damage: int) -> int:
                return int(damage * (1 + self.value / 100))  # Convert 50 to 50%
            
            def update(self) -> bool:
                return True  # Permanent buff
            
            def get_tooltip_title(self) -> str:
                return "Ice Blade"
            
            def get_tooltip_text(self) -> str:
                return f"Damage increased by {self.value}%\nPermanent effect"
        
        # Apply the buff
        buff = IceBladeBuff(self.icon)
        target.add_buff(buff)
        self.stack_count -= 1  # Use one from the stack
        
        # Log the buff
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  {target.name} gains Ice Blade: Damage increased by 50%",
                GameEngine.instance.battle_log.BUFF_COLOR
            )
        
        return True

    def draw_tooltip(self, screen: pygame.Surface):
        if not self.is_hovered:
            return
            
        padding = 16
        line_spacing = 6
        
        # Prepare text surfaces with shadows
        title_font = pygame.font.Font(None, 32)
        desc_font = pygame.font.Font(None, 26)
        detail_font = pygame.font.Font(None, 24)
        
        title_shadow = title_font.render(self.name, True, (0, 0, 0))
        title_surface = title_font.render(self.name, True, self.RARITY_COLORS["Legendary"])  # Use legendary color
        desc_surface = desc_font.render(self.description, True, (220, 220, 220))
        
        # Prepare effect text
        effect_lines = [
            "Effects:",
            "• Increases damage by 50%",
            "• Permanent effect",
            "• Does not end turn"
        ]
        effect_surfaces = [detail_font.render(line, True, (220, 220, 220)) for line in effect_lines]
        
        # Calculate tooltip dimensions
        width = max(
            title_surface.get_width(),
            desc_surface.get_width(),
            *[surface.get_width() for surface in effect_surfaces]
        ) + padding * 3
        
        height = (padding * 2 + title_surface.get_height() + line_spacing +
                 desc_surface.get_height() + line_spacing * 2 +
                 sum(surface.get_height() + line_spacing for surface in effect_surfaces))
        
        # Position tooltip to the right of the item
        x = self.position[0] + self.icon.get_width() + 10
        y = self.position[1]
        
        # Keep tooltip on screen
        if x + width > screen.get_width():
            x = self.position[0] - width - 10
        if y + height > screen.get_height():
            y = screen.get_height() - height
        
        # Draw tooltip shadow
        shadow_rect = pygame.Rect(x + 4, y + 4, width, height)
        pygame.draw.rect(screen, (0, 0, 0, 60), shadow_rect, border_radius=10)
        
        # Draw main tooltip background
        tooltip_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, (32, 36, 44, 240), tooltip_rect, border_radius=10)
        
        # Draw border with gradient effect
        border_rect = tooltip_rect.inflate(2, 2)
        pygame.draw.rect(screen, (64, 68, 76), border_rect, width=2, border_radius=10)
        inner_border = tooltip_rect.inflate(-2, -2)
        pygame.draw.rect(screen, (80, 84, 92), inner_border, width=1, border_radius=9)
        
        current_y = y + padding
        
        # Draw title with shadow
        screen.blit(title_shadow, (x + padding + 1, current_y + 1))
        screen.blit(title_surface, (x + padding, current_y))
        current_y += title_surface.get_height() + line_spacing
        
        # Draw separator line
        separator_y = current_y - line_spacing//2
        pygame.draw.line(screen, (80, 84, 92),
                        (x + padding, separator_y),
                        (x + width - padding, separator_y))
        
        # Draw description
        screen.blit(desc_surface, (x + padding, current_y))
        current_y += desc_surface.get_height() + line_spacing * 2
        
        # Draw effects
        for i, effect_surface in enumerate(effect_surfaces):
            # Draw shadow for each line
            shadow = detail_font.render(effect_lines[i], True, (0, 0, 0))
            screen.blit(shadow, (x + padding + 1, current_y + 1))
            screen.blit(effect_surface, (x + padding, current_y))
            current_y += effect_surface.get_height() + line_spacing 

class ZasalamelsScythe(Item):
    def __init__(self):
        super().__init__(
            name="Zasalamel's Scythe",
            description="A legendary scythe that can reap the souls of all enemies at once.",
            rarity="Legendary",
            item_type="Consumable",
            icon_path="assets/items/zasalamel_scythe.png",
            max_stack=1  # Legendary item, can't stack
        )
        self.cooldown = 50  # 50 turns cooldown
        self.ends_turn = True  # Using this powerful item ends your turn
    
    def use(self, user: Character, target: Character) -> bool:
        """Deal massive damage to all enemies, ignoring armor and damage reduction."""
        # Call base class use method to log the use
        if not super().use(user, target):
            return False
        
        # Get game engine instance for accessing all enemies
        from engine.game_engine import GameEngine
        if not GameEngine.instance or not GameEngine.instance.stage_manager.current_stage:
            return False
            
        # Deal damage to all enemies
        damage = 5000
        enemies = GameEngine.instance.stage_manager.current_stage.bosses
        for enemy in enemies:
            if enemy.is_alive() and enemy.is_targetable():
                # Bypass armor and damage reduction by directly setting health
                current_health = enemy.stats.current_hp
                new_health = max(0, current_health - damage)
                enemy.stats.current_hp = new_health
                
                # Log the damage
                GameEngine.instance.battle_log.add_message(
                    f"  {enemy.name} takes {damage} unblockable damage from Zasalamel's Scythe!",
                    GameEngine.instance.battle_log.DAMAGE_COLOR
                )
                
                # Check if enemy died
                if new_health == 0:
                    GameEngine.instance.battle_log.add_message(
                        f"  {enemy.name} has been reaped by Zasalamel's Scythe!",
                        GameEngine.instance.battle_log.CRITICAL_COLOR
                    )
        
        self.stack_count -= 1  # Use one from the stack
        return True
    
    def draw_tooltip(self, screen: pygame.Surface):
        if not self.is_hovered:
            return
            
        padding = 16
        line_spacing = 6
        
        # Prepare text surfaces with shadows
        title_font = pygame.font.Font(None, 32)
        desc_font = pygame.font.Font(None, 26)
        detail_font = pygame.font.Font(None, 24)
        
        title_shadow = title_font.render(self.name, True, (0, 0, 0))
        title_surface = title_font.render(self.name, True, self.RARITY_COLORS.get(self.rarity, (255, 255, 255)))
        desc_surface = desc_font.render(self.description, True, (220, 220, 220))
        
        # Prepare effect text
        effect_lines = [
            "Effects:",
            "• Deals 5000 unblockable damage to ALL enemies",
            "• Ignores armor and damage reduction",
            "• Cooldown: 50 turns",
            "• Ends your turn"
        ]
        effect_surfaces = [detail_font.render(line, True, (220, 220, 220)) for line in effect_lines]
        
        # Calculate tooltip dimensions
        width = max(
            title_surface.get_width(),
            desc_surface.get_width(),
            *[surface.get_width() for surface in effect_surfaces]
        ) + padding * 3
        
        height = (padding * 2 + title_surface.get_height() + line_spacing +
                 desc_surface.get_height() + line_spacing * 2 +
                 sum(surface.get_height() + line_spacing for surface in effect_surfaces))
        
        # Position tooltip to the right of the item
        x = self.position[0] + self.icon.get_width() + 10
        y = self.position[1]
        
        # Keep tooltip on screen
        screen_rect = screen.get_rect()
        if x + width > screen_rect.width:
            x = self.position[0] - width - 10
        if y + height > screen_rect.height:
            y = screen_rect.height - height
        if y < 0:
            y = 0
        
        # Draw tooltip background with border
        tooltip_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, self.TOOLTIP_BG_COLOR, tooltip_rect, border_radius=10)
        pygame.draw.rect(screen, self.TOOLTIP_BORDER_COLOR, tooltip_rect, width=2, border_radius=10)
        
        # Draw title with shadow
        current_y = y + padding
        screen.blit(title_shadow, (x + padding + 1, current_y + 1))
        screen.blit(title_surface, (x + padding, current_y))
        current_y += title_surface.get_height() + line_spacing
        
        # Draw separator line
        pygame.draw.line(screen, self.TOOLTIP_BORDER_COLOR,
                        (x + padding, current_y - line_spacing//2),
                        (x + width - padding, current_y - line_spacing//2))
        
        # Draw description
        screen.blit(desc_surface, (x + padding, current_y))
        current_y += desc_surface.get_height() + line_spacing * 2
        
        # Draw effects
        for i, effect_surface in enumerate(effect_surfaces):
            # Draw shadow for each line
            shadow = detail_font.render(effect_lines[i], True, (0, 0, 0))
            screen.blit(shadow, (x + padding + 1, current_y + 1))
            screen.blit(effect_surface, (x + padding, current_y))
            current_y += effect_surface.get_height() + line_spacing 