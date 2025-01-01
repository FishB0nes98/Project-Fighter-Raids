from items.base_item import Item
from characters.base_character import Character, StatusEffect
import pygame

class PiranhaScales(Item):
    def __init__(self):
        super().__init__(
            name="Piranha Scales",
            description="Tough scales that provide natural armor, protecting against enemy attacks.",
            rarity="Common",
            item_type="Buff",
            icon_path="assets/items/Piranha_Scales.png",
            max_stack=10  # Allow stacking up to 10 scales
        )
        self.cooldown = 20  # 20 turns cooldown
    
    def use(self, user: Character, target: Character) -> bool:
        """Apply armor buff to the target."""
        # Check if target already has a defense buff
        if any(buff.type == "defense" for buff in target.buffs):
            return False
        
        # Call base class use method to log the use
        super().use(user, target)
        
        # Apply buff
        buff = StatusEffect("defense", 25, 3, self.icon)  # +25 armor for 3 turns
        target.add_buff(buff)
        self.stack_count -= 1  # Use one from the stack
        
        # Log the buff
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  Increases {target.name}'s armor by 25 for 3 turns",
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
        title_surface = title_font.render(self.name, True, (255, 255, 255))
        desc_surface = desc_font.render(self.description, True, (220, 220, 220))
        
        # Prepare effect text
        effect_lines = [
            "Effects:",
            "• Increases armor by 25",
            "• Lasts 3 turns",
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

class TidalCharm(Item):
    def __init__(self):
        super().__init__(
            name="Tidal Charm",
            description="A mystical charm that enhances healing effects.",
            rarity="Common",
            item_type="Buff",
            icon_path="assets/items/Tidal_Charm.png",
            max_stack=5
        )
        self.cooldown = 20  # 20 turns cooldown

    def use(self, user: Character, target: Character) -> bool:
        """Apply healing boost buff to the target."""
        # Check if target already has a Tidal Blessing buff
        if any(hasattr(buff, 'name') and buff.name == "Tidal Blessing" for buff in target.buffs):
            return False
        
        # Call base class use method to log the use
        super().use(user, target)
        
        # Create a custom buff that increases healing received
        class HealingBoostBuff(StatusEffect):
            def __init__(self, icon):
                super().__init__("custom", 50, 5, icon)  # Changed type to "custom" for proper tooltip display
                self.name = "Tidal Blessing"
                self.description = "Healing received increased by 50%"
            
            def modify_healing_received(self, healing: int) -> int:
                return int(healing * (1 + self.value / 100))  # Increase healing by percentage
            
            def update(self) -> bool:
                self.duration -= 1
                return self.duration > 0
            
            def get_tooltip_title(self) -> str:
                return "Tidal Blessing"
            
            def get_tooltip_text(self) -> str:
                return f"Healing received increased by {self.value}%\n{self.duration} turns remaining"
        
        # Apply the buff
        buff = HealingBoostBuff(self.icon)
        target.add_buff(buff)
        self.stack_count -= 1  # Use one from the stack
        
        # Log the buff
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  {target.name} gains Tidal Blessing: +50% healing received for 5 turns",
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
        title_surface = title_font.render(self.name, True, (255, 255, 255))
        desc_surface = desc_font.render(self.description, True, (220, 220, 220))
        
        # Prepare effect text
        effect_lines = [
            "Effects:",
            "• Increases healing received by 50%",
            "• Lasts 5 turns",
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

class VoidEssence(Item):
    def __init__(self):
        super().__init__(
            name="Void Essence",
            description="A dark essence that empowers your abilities with chaotic energy.",
            rarity="Rare",
            item_type="Buff",
            icon_path="assets/items/Void_Essence.png",
            max_stack=5
        )
        self.cooldown = 100  # 100 turns cooldown

    def use(self, user: Character, target: Character) -> bool:
        """Apply double damage chance buff to the target."""
        # Check if target already has a double damage chance buff
        if any(buff.type == "double_damage_chance" for buff in target.buffs):
            return False
        
        # Call base class use method to log the use
        super().use(user, target)
        
        # Create a custom buff that gives a chance for double damage
        class DoubleDamageChanceBuff(StatusEffect):
            def __init__(self, icon):
                super().__init__("double_damage_chance", 25, 8, icon)  # 25% chance for 8 turns
                self.name = "Void Empowerment"
                self.description = "Your abilities have a chance to deal double damage."
            
            def modify_damage_dealt(self, damage: int) -> int:
                import random
                if random.random() < self.value / 100:  # value% chance
                    # Log the double damage proc
                    from engine.game_engine import GameEngine
                    if GameEngine.instance:
                        GameEngine.instance.battle_log.add_message(
                            "  Void Empowerment triggers: Double damage!",
                            GameEngine.instance.battle_log.CRIT_COLOR
                        )
                    return damage * 2
                return damage
            
            def update(self) -> bool:
                self.duration -= 1
                return self.duration > 0
            
            def get_tooltip_title(self) -> str:
                return "Void Empowerment"
            
            def get_tooltip_text(self) -> str:
                return f"Your abilities are empowered with chaotic energy.\n\nEffects:\n• {self.value}% chance to deal double damage\n• {self.duration} turns remaining"
        
        # Apply the buff
        buff = DoubleDamageChanceBuff(self.icon)
        target.add_buff(buff)
        self.stack_count -= 1  # Use one from the stack
        
        # Log the buff
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  {target.name} gains Void Empowerment: 25% chance to deal double damage for 8 turns",
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
        title_surface = title_font.render(self.name, True, (255, 255, 255))
        desc_surface = desc_font.render(self.description, True, (220, 220, 220))
        
        # Prepare effect text
        effect_lines = [
            "Effects:",
            "• 25% chance to deal double damage",
            "• Lasts 8 turns",
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
    
    def use(self, user: Character, target: Character) -> bool:
        """Apply permanent damage increase buff to the target."""
        # Call base class use method to log the use
        super().use(user, target)
        
        # Create a custom buff that increases damage dealt
        class IceBladeBuff(StatusEffect):
            def __init__(self, icon):
                super().__init__("custom", 50, -1, icon)  # Permanent buff
                self.name = "Ice Blade"
                self.description = "Damage increased by 50%"
            
            def modify_damage_dealt(self, damage: int) -> int:
                return int(damage * 1.5)  # 50% damage increase
            
            def update(self) -> bool:
                """Return True to keep the buff active"""
                return True  # Permanent buff
            
            def get_tooltip_title(self) -> str:
                return "Ice Blade"
            
            def get_tooltip_text(self) -> str:
                return "Damage increased by 50%\nPermanent effect"
        
        # Apply the buff
        buff = IceBladeBuff(self.icon)
        target.add_buff(buff)
        self.stack_count -= 1  # Use one from the stack
        
        # Log the buff
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  {target.name} gains Ice Blade: +50% damage dealt permanently",
                GameEngine.instance.battle_log.BUFF_COLOR
            )
        
        return True

class ShadowDagger(Item):
    def __init__(self):
        super().__init__(
            name="Shadow Dagger",
            description="A dagger infused with dark energy that doubles damage but causes self-damage.",
            rarity="Epic",
            item_type="Buff",
            icon_path="assets/items/Shadow_Dagger.png",
            max_stack=3
        )
        self.cooldown = 50  # 50 turns cooldown
    
    def use(self, user: Character, target: Character) -> bool:
        """Apply the shadow buff that increases damage but causes self-damage."""
        # Check if target already has a shadow buff
        if any(hasattr(buff, 'name') and buff.name == "Shadow's Embrace" for buff in target.buffs):
            return False
        
        # Call base class use method to log the use
        super().use(user, target)
        
        # Create and apply the shadow buff
        buff = ShadowEmbraceBuff(self.icon)
        target.add_buff(buff)
        return True

class ShadowEmbraceBuff(StatusEffect):
    def __init__(self, icon):
        super().__init__("custom", 100, 10, icon)  # 100% increase (double damage) for 10 turns
        self.name = "Shadow's Embrace"
        self.description = "Your abilities deal double damage but you take 20% of damage dealt as self-damage. Abilities cost no mana."
        self.target = None
    
    def apply_damage_increase(self, damage: int) -> int:
        """Double damage while buff is active"""
        if self.duration <= 0:
            return damage
        return damage * 2
    
    def on_damage_dealt(self, damage: int):
        """Apply 20% self-damage after dealing damage"""
        if self.duration <= 0 or not self.target:
            return
        
        self_damage = int(damage * 0.2)  # 20% of damage dealt
        if self_damage > 0:
            self.target.take_damage(self_damage)
    
    def modify_mana_cost(self, cost: int) -> int:
        """Remove mana costs while buff is active"""
        return 0 if self.duration > 0 else cost
    
    def update(self) -> bool:
        """Update buff duration"""
        self.duration -= 1
        self.description = f"Your abilities deal double damage but you take 20% of damage dealt as self-damage. Abilities cost no mana.\n{self.duration} turns remaining"
        return self.duration > 0
    
    def get_tooltip_title(self) -> str:
        return "Shadow's Embrace"
    
    def get_tooltip_text(self) -> str:
        effects = [
            "Dark energy empowers your strikes:",
            "• Your abilities deal double damage",
            "• You take 20% of damage dealt as self-damage",
            "• Your abilities cost no mana",
            f"• {self.duration} turns remaining"
        ]
        return "\n".join(effects)
    
    def on_apply(self, target: Character):
        self.target = target
    
    def on_remove(self, target: Character):
        self.target = None