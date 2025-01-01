from items.base_item import Item
from characters.base_character import Character, StatusEffect
from abilities.base_ability import Ability
import pygame
from typing import List

class MurkyWaterVial(Item):
    def __init__(self):
        super().__init__(
            name="Murky Water Vial",
            description="A vial of murky water that restores 500 HP.",
            rarity="Common",
            item_type="Consumable",
            icon_path="assets/items/murky_water_vial.png",
            max_stack=10
        )
        self.cooldown = 7  # 7 turns cooldown
    
    def use(self, user: Character, target: Character) -> bool:
        """Use the vial to restore health."""
        # Call base class use method to log the use
        super().use(user, target)
        
        # Calculate healing amount with buffs
        heal_amount = 500
        for buff in target.buffs:
            if hasattr(buff, 'modify_healing_received'):
                heal_amount = buff.modify_healing_received(heal_amount)
        
        # Heal the target
        target.heal(heal_amount)
        self.stack_count -= 1  # Use one from the stack
        
        # Log the heal
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  {target.name} is healed for {heal_amount} HP",
                GameEngine.instance.battle_log.HEAL_COLOR
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
            "• Restores 500 HP",
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

class PiranhaTooth(Item):
    def __init__(self):
        super().__init__(
            name="Piranha Tooth",
            description="A razor-sharp tooth that empowers your abilities with the piranha's ferocity.",
            rarity="Common",
            item_type="Consumable",
            icon_path="assets/items/Piranha_Tooth.png",
            max_stack=5
        )
        self.cooldown = 20  # 20 turns cooldown
    
    def use(self, user: Character, target: Character) -> bool:
        """Apply damage boost buff to the target."""
        # Check if target already has a damage boost buff
        if any(buff.type == "damage_boost" for buff in target.buffs):
            return False
        
        # Call base class use method to log the use
        super().use(user, target)
        
        # Create a custom buff that adds flat damage to abilities
        class DamageBoostBuff(StatusEffect):
            def __init__(self, icon):
                super().__init__("custom", 40, 10, icon)  # Use custom type to enable custom tooltips
                self.name = "Piranha's Bite"
                self.description = "Your abilities are empowered with the piranha's ferocity."
            
            def apply_damage_increase(self, damage: int) -> int:
                return damage + self.value  # Add flat damage bonus
            
            def update(self) -> bool:
                self.duration -= 1
                return self.duration > 0
            
            def get_tooltip_title(self) -> str:
                return "Piranha's Bite"
            
            def get_tooltip_text(self) -> str:
                return f"Your abilities are empowered with the piranha's ferocity.\n\nEffects:\n• Increases ability damage by {self.value}\n• {self.duration} turns remaining"
        
        # Apply the buff
        buff = DamageBoostBuff(self.icon)
        target.add_buff(buff)
        self.stack_count -= 1  # Use one from the stack
        
        # Log the buff
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  {target.name} gains Piranha's Bite: +40 damage to abilities for 10 turns",
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
            "• Adds 40 bonus damage to all abilities",
            "• Lasts 10 turns",
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

class FishOilFlask(Item):
    def __init__(self):
        super().__init__(
            name="Fish Oil Flask",
            description="A flask of fish oil that increases speed by 20% for 3 turns. Ends your turn.",
            rarity="Common",
            item_type="Consumable",
            icon_path="assets/items/Fish_Oil_Flask.png",
            max_stack=5  # Allow stacking up to 5 flasks
        )
    
    def use(self, user: Character, target: Character) -> bool:
        """Use the flask to boost speed."""
        # Check if target already has a speed buff
        if any(buff.type == "speed" for buff in target.buffs):
            return False
        
        # Call base class use method to log the use
        super().use(user, target)
        
        # Apply speed buff
        buff = StatusEffect("speed", 20, 3, self.icon)  # 20% speed increase for 3 turns
        target.add_buff(buff)
        self.stack_count -= 1  # Use one from the stack
        
        # Log the buff
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  Increases {target.name}'s speed by 20% for 3 turns",
                GameEngine.instance.battle_log.BUFF_COLOR
            )
        
        return True 

class DeepSeaEssence(Item):
    def __init__(self):
        super().__init__(
            name="Deep Sea Essence",
            description="A mysterious essence from the ocean depths.",
            rarity="Rare",
            item_type="Consumable",
            icon_path="assets/items/Deep_Sea_Essence.png",
            max_stack=5
        )
        self.cooldown = 100  # 100 turns cooldown

    def use(self, user: Character, target: Character) -> bool:
        """Use the essence to restore mana and reduce cooldowns."""
        # Call base class use method to log the use
        super().use(user, target)
        
        # Restore mana
        target.restore_mana(1000)
        
        # Reduce all ability cooldowns by 1
        for ability in target.abilities:
            if ability.current_cooldown > 0:
                ability.current_cooldown = max(0, ability.current_cooldown - 1)
        
        self.stack_count -= 1  # Use one from the stack
        
        # Log the effects
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  {target.name} restores 1000 mana and reduces all cooldowns by 1 turn",
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
            "• Restores 1000 mana",
            "• Reduces all ability cooldowns by 1 turn",
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

class IceShard(Item):
    def __init__(self):
        super().__init__(
            name="Ice Shard",
            description="A sharp shard of magical ice that deals heavy damage.",
            rarity="Common",
            item_type="Damage",
            icon_path="assets/items/ice_shard.png",
            max_stack=10
        )
        self.ends_turn = False  # This item does not end the turn when used
        self.cooldown = 10  # 10 turns cooldown
    
    def use(self, user: Character, target: Character) -> bool:
        """Deal direct damage to the target."""
        # Call base class use method to log the use
        super().use(user, target)
        
        # Deal damage
        damage = 555
        target.take_damage(damage)
        self.stack_count -= 1  # Use one from the stack
        
        # Log the damage
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  {user.name} throws an Ice Shard at {target.name} for {damage} damage!",
                GameEngine.instance.battle_log.DAMAGE_COLOR
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
        title_surface = title_font.render(self.name, True, self.RARITY_COLORS["Common"])  # Use common color
        desc_surface = desc_font.render(self.description, True, (220, 220, 220))
        
        # Prepare effect text
        effect_lines = [
            "Effects:",
            "• Deals 555 damage",
            "• Can target enemies",
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

class IceFlask(Item):
    def __init__(self):
        super().__init__(
            name="Ice Flask",
            description="A flask filled with magical ice. Used in crafting.",
            rarity="Common",
            item_type="Material",
            icon_path="assets/items/ice_flask.png",
            max_stack=10
        )
        self.ends_turn = False  # Materials don't end the turn
    
    def use(self, user: Character, target: Character) -> bool:
        """Materials cannot be used directly."""
        return False  # Return False to indicate the item cannot be used 

class CursedWaterVial(Item):
    def __init__(self):
        super().__init__(
            name="Cursed Water Vial",
            description="A vial of cursed water from the depths. Used in crafting.",
            rarity="Common",
            item_type="Material",
            icon_path="assets/items/cursed_water_vial.png",
            max_stack=10
        )
        self.ends_turn = False  # Materials don't end the turn
    
    def use(self, user: Character, target: Character) -> bool:
        """Materials cannot be used directly."""
        return False  # Return False to indicate the item cannot be used 

class IceDagger(Item):
    def __init__(self):
        super().__init__(
            name="Ice Dagger",
            description="A dagger infused with frost magic. Reduces all ability cooldowns by 3 turns.",
            rarity="Common",
            item_type="Utility",
            icon_path="assets/items/ice_dagger.png",
            max_stack=10
        )
        self.ends_turn = False  # This item does not end the turn when used
        self.cooldown = 6  # 6 turns cooldown
    
    def use(self, user: Character, target: Character) -> bool:
        """Reduce all ability cooldowns of the target by 3 turns."""
        # Call base class use method to log the use
        super().use(user, target)
        
        # Reduce cooldowns
        for ability in target.abilities:
            if ability.current_cooldown > 0:
                ability.current_cooldown = max(0, ability.current_cooldown - 3)
        
        self.stack_count -= 1  # Use one from the stack
        
        # Log the effect
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  {user.name} uses Ice Dagger on {target.name}, reducing all ability cooldowns by 3!",
                GameEngine.instance.battle_log.BUFF_COLOR
            )
        
        return True 

class SmokeBomb(Item):
    def __init__(self):
        super().__init__(
            name="Smoke Bomb",
            description="Envelops the target in a cloud of smoke, making them untargetable for 4 turns.",
            rarity="Rare",
            item_type="Consumable",
            icon_path="assets/items/smoke_bomb.png",
            max_stack=5
        )
        print("[DEBUG] SmokeBomb initialized")
        
    def use(self, user: Character, target: Character) -> bool:
        """Apply stealth effect to the target"""
        print(f"\n[DEBUG] Attempting to use Smoke Bomb on target: {target.name}")
        print(f"[DEBUG] Target alive status: {target.is_alive()}")
        
        if not target.is_alive():
            print("[DEBUG] Failed - Target is not alive")
            return False
            
        # Call base class use method to log the use
        super().use(user, target)
            
        # Create stealth buff
        class StealthBuff(StatusEffect):
            def __init__(self, icon):
                super().__init__("stealth", 0, 4, icon)
                self.name = "Smoke Screen"
                self.description = "Untargetable from Smoke Bomb"
                self.original_alpha = None
                self.target = None
                print("[DEBUG] StealthBuff created with duration:", self.duration)
                
            def update(self):
                """Update duration and return True if buff should continue"""
                self.duration -= 1
                self.description = f"Untargetable from Smoke Bomb\n{self.duration} turns remaining"
                print(f"[DEBUG] StealthBuff updated - {self.duration} turns remaining")
                
                # If buff is expiring, restore opacity
                if self.duration <= 0 and self.target:
                    if self.original_alpha is not None:
                        self.target.image.set_alpha(self.original_alpha)
                        print("[DEBUG] Restored original alpha:", self.original_alpha)
                    from engine.game_engine import GameEngine
                    if GameEngine.instance:
                        GameEngine.instance.battle_log.add_message(
                            f"{self.target.name} emerges from the shadows!",
                            GameEngine.instance.battle_log.TEXT_COLOR
                        )
                
                return self.duration > 0
                
            def is_stealthed(self):
                """Return True while buff is active"""
                print("[DEBUG] Checking stealth status:", self.duration > 0)
                return self.duration > 0
                
            def get_tooltip_title(self):
                return "Smoke Screen"
                
            def get_tooltip_text(self):
                return f"Untargetable for {self.duration} more turns"
                
            def on_apply(self, target: Character):
                """Called when the buff is applied"""
                print("[DEBUG] Applying stealth buff to target:", target.name)
                self.target = target
                self.original_alpha = target.image.get_alpha()
                target.image.set_alpha(51)  # 20% opacity
                print("[DEBUG] Set alpha to 51 (20% opacity)")
                
            def on_remove(self, target: Character):
                """Called when the buff is removed"""
                print("[DEBUG] Removing stealth buff from target:", target.name)
                if self.original_alpha is not None:
                    target.image.set_alpha(self.original_alpha)
                    print("[DEBUG] Restored original alpha:", self.original_alpha)
                
            def is_targetable(self):
                """Return False to make character untargetable"""
                return False
        
        # Apply the stealth buff
        buff = StealthBuff(self.icon)
        print("[DEBUG] Adding stealth buff to target")
        target.add_buff(buff)
        
        # Log the effect
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            print("[DEBUG] Logging effect to battle log")
            GameEngine.instance.battle_log.add_message(
                f"{target.name} is shrouded in smoke!",
                GameEngine.instance.battle_log.BUFF_COLOR
            )
        
        self.stack_count -= 1  # Use one from the stack
        print("[DEBUG] Smoke Bomb successfully used\n")
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
            "• Makes target untargetable",
            "• Lasts 4 turns",
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

class LeviathanMistVial(Item):
    def __init__(self):
        super().__init__(
            name="Leviathan's Mist Vial",
            description="A mystical vial containing the essence of the Leviathan. Recovers 20% HP and grants Abyssal Regeneration.",
            rarity="Rare",
            item_type="Consumable",
            icon_path="assets/items/leviathan_mist_vial.png",
            max_stack=5
        )
    
    def use(self, user: Character, target: Character) -> bool:
        """Apply healing and Abyssal Regeneration buff to the target."""
        # Call base class use method to log the use
        super().use(user, target)
        
        # Calculate and apply instant healing
        heal_amount = int(target.stats.max_hp * 0.20)  # 20% max HP
        target.heal(heal_amount)
        
        # Create and apply the Abyssal Regeneration buff
        class AbyssalRegenBuff(StatusEffect):
            def __init__(self, character: Character):
                super().__init__("custom", 88, 2, pygame.image.load("assets/buffs/abyssal_regen.png"))
                self.name = "Abyssal Regeneration"
                self.description = "Regenerates 88 HP at the end of each turn"
                self._character = character
                self.heal_per_turn = 88  # Same as boss's healing amount
            
            def update(self) -> bool:
                """Update duration and return True if buff should continue"""
                if self.duration > 0:
                    # Apply healing at end of turn
                    self._character.heal(self.heal_per_turn)
                    # Log the healing
                    from engine.game_engine import GameEngine
                    if GameEngine.instance:
                        GameEngine.instance.battle_log.add_message(
                            f"  {self._character.name} regenerates {self.heal_per_turn} HP from Abyssal Regeneration",
                            GameEngine.instance.battle_log.HEAL_COLOR
                        )
                
                self.duration -= 1
                self.description = f"Regenerates {self.heal_per_turn} HP at the end of each turn\n{self.duration} turns remaining"
                return self.duration > 0
            
            def get_tooltip_title(self) -> str:
                return "Abyssal Regeneration"
            
            def get_tooltip_text(self) -> str:
                if self.duration > 0:
                    return f"Regenerates {self.heal_per_turn} HP at the end of each turn\n{self.duration} turns remaining"
                return "Abyssal Regeneration has expired"
        
        # Apply the buff
        buff = AbyssalRegenBuff(target)
        target.add_buff(buff)
        
        # Log the effects
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  {target.name} recovers {heal_amount} HP and gains Abyssal Regeneration!",
                GameEngine.instance.battle_log.HEAL_COLOR
            )
        
        # Reduce stack count by 1 when used
        self.stack_count -= 1
        
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
        title_surface = title_font.render(self.name, True, self.RARITY_COLORS["Rare"])  # Use Rare color
        desc_surface = desc_font.render(self.description, True, (220, 220, 220))
        
        # Prepare effect text
        effect_lines = [
            "Effects:",
            "• Recovers 20% max HP instantly",
            "• Grants Abyssal Regeneration for 2 turns",
            "  (Regenerates 88 HP at end of each turn)",
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

class AbyssalEcho(Item):
    def __init__(self):
        super().__init__(
            name="Abyssal Echo",
            description="Echoes the power of a random ability, making it cost no mana for 30 turns.",
            rarity="Epic",
            item_type="Consumable",
            icon_path="assets/items/abyssal_echo.png",
            max_stack=5
        )
        self.cooldown = 15  # 15 turns cooldown
    
    def use(self, user: Character, target: Character) -> bool:
        """Apply the Abyssal Echo buff to a random ability."""
        # Call base class use method to log the use
        super().use(user, target)
        
        # Get non-passive abilities that aren't already echoed
        available_abilities = [
            ability for ability in target.abilities 
            if not hasattr(ability, 'is_passive') and 
            not any(isinstance(buff, AbyssalEchoBuff) and buff.echoed_ability == ability for buff in target.buffs)
        ]
        
        if not available_abilities:
            # Log failure if no available abilities
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    f"  No available abilities to echo on {target.name}!",
                    GameEngine.instance.battle_log.TEXT_COLOR
                )
            return False
        
        # Choose random ability to echo
        import random
        ability_to_echo = random.choice(available_abilities)
        
        # Create and apply the buff
        buff = AbyssalEchoBuff(ability_to_echo, self.icon)
        target.add_buff(buff)
        
        # Log the effect
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  {target.name}'s {ability_to_echo.name} is echoed - now costs no mana for 30 turns!",
                GameEngine.instance.battle_log.BUFF_COLOR
            )
        
        self.stack_count -= 1  # Use one from the stack
        return True

class AbyssalEchoBuff(StatusEffect):
    def __init__(self, ability: Ability, icon: pygame.Surface):
        super().__init__("custom", 30, 30, icon)
        self.name = "Abyssal Echo"
        self.description = f"{ability.name} costs no mana"
        self.echoed_ability = ability
        
        # Store original mana cost and create modified use function
        self.original_mana_cost = ability.mana_cost
        self.original_use = ability.use
        
        # Override the ability's use method to cost no mana
        def no_mana_use(caster: Character, targets: List[Character]) -> bool:
            # Temporarily set mana cost to 0
            old_mana_cost = self.echoed_ability.mana_cost
            self.echoed_ability.mana_cost = 0
            
            # Call original use method
            result = self.original_use(caster, targets)
            
            # Restore original mana cost
            self.echoed_ability.mana_cost = old_mana_cost
            return result
        
        ability.use = no_mana_use
    
    def update(self) -> bool:
        """Update the buff duration"""
        self.duration -= 1
        self.description = f"{self.echoed_ability.name} costs no mana\n{self.duration} turns remaining"
        
        if self.duration <= 0:
            # Restore original use method when buff expires
            self.echoed_ability.use = self.original_use
            return False
        return True
    
    def get_tooltip_title(self) -> str:
        return f"Abyssal Echo: {self.echoed_ability.name}"
    
    def get_tooltip_text(self) -> str:
        return f"The depths echo through {self.echoed_ability.name}, removing its mana cost.\n\nEffects:\n• {self.echoed_ability.name} costs 0 mana\n• Original cost: {self.original_mana_cost}\n• {self.duration} turns remaining" 

class ManaPotion(Item):
    def __init__(self):
        super().__init__(
            name="Mana Potion",
            description="A mystical potion that restores 700 mana.",
            rarity="Common",
            item_type="Consumable",
            icon_path="assets/items/mana_potion.png",
            max_stack=10
        )
        self.cooldown = 5  # 5 turns cooldown
    
    def use(self, user: Character, target: Character) -> bool:
        """Use the potion to restore mana."""
        # Call base class use method to log the use
        super().use(user, target)
        
        # Restore mana
        target.restore_mana(700)
        self.stack_count -= 1  # Use one from the stack
        
        # Log the effect
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"  {target.name} restores 700 mana",
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
        title_surface = title_font.render(self.name, True, self.RARITY_COLORS["Common"])
        desc_surface = desc_font.render(self.description, True, (220, 220, 220))
        
        # Prepare effect text
        effect_lines = [
            "Effects:",
            "• Restores 700 mana",
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

class AtlanteanTrident(Item):
    def __init__(self):
        super().__init__(
            name="Atlantean Trident of Time Manipulation",
            description="A legendary trident imbued with the Dark Leviathan's power over time. Accelerates ability cooldowns for all allies.",
            rarity="Epic",
            item_type="Consumable",
            icon_path="assets/items/atlantean_trident_time.png",
            max_stack=1
        )
        self.cooldown = 50  # 50 turns cooldown
    
    def use(self, user: Character, target: Character) -> bool:
        """Apply cooldown reduction buff to all player characters."""
        # Call base class use method to log the use
        super().use(user, target)
        
        # Get all player characters
        from engine.game_engine import GameEngine
        if not GameEngine.instance:
            return False
            
        # Apply buff to all player characters
        for character in GameEngine.instance.stage_manager.player_characters:
            if character.is_alive():
                buff = TimeManipulationBuff(self.icon)
                character.add_buff(buff)
        
        # Log the effect
        GameEngine.instance.battle_log.add_message(
            "The Atlantean Trident pulses with temporal energy!",
            GameEngine.instance.battle_log.BUFF_COLOR
        )
        GameEngine.instance.battle_log.add_message(
            "  All allies' ability cooldowns are accelerated!",
            GameEngine.instance.battle_log.BUFF_COLOR
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
        title_surface = title_font.render(self.name, True, self.RARITY_COLORS["Epic"])
        desc_surface = desc_font.render(self.description, True, (220, 220, 220))
        
        # Prepare effect text
        effect_lines = [
            "Effects:",
            "• Reduces all allies' ability cooldowns by 1 each turn",
            "• Effect lasts 4 turns",
            "• 50 turn cooldown",
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

class TimeManipulationBuff(StatusEffect):
    def __init__(self, icon: pygame.Surface):
        super().__init__("custom", 1, 4, icon)  # 4 turns duration, value=1 for cooldown reduction
        self.name = "Time Manipulation"
        self.description = "Ability cooldowns are accelerated"
    
    def on_apply(self, character: Character):
        """Called when the buff is first applied to a character"""
        self._character = character
    
    def update(self) -> bool:
        """Update buff duration and reduce cooldowns"""
        # Only reduce cooldowns if we still have duration left
        if self.duration > 0:
            # Reduce all ability cooldowns by 1 (stacks with normal reduction)
            if hasattr(self, '_character') and self._character:
                reduced_any = False  # Track if we actually reduced any cooldowns
                
                for ability in self._character.abilities:
                    if ability.current_cooldown > 0:
                        old_cooldown = ability.current_cooldown
                        ability.current_cooldown = max(0, ability.current_cooldown - self.value)
                        if old_cooldown != ability.current_cooldown:
                            reduced_any = True
                
                # Only log if we actually reduced some cooldowns
                if reduced_any:
                    from engine.game_engine import GameEngine
                    if GameEngine.instance:
                        GameEngine.instance.battle_log.add_message(
                            f"  {self._character.name}'s ability cooldowns are accelerated!",
                            GameEngine.instance.battle_log.BUFF_COLOR
                        )
            
            # Update description before reducing duration
            self.description = f"Ability cooldowns are accelerated\n{self.duration} turns remaining"
            # Reduce duration after effects
            self.duration -= 1
            return True
        
        return False
    
    def get_tooltip_title(self) -> str:
        return "Time Manipulation"
    
    def get_tooltip_text(self) -> str:
        return f"The Atlantean Trident bends time around you, accelerating your abilities.\n\nEffects:\n• Reduces all ability cooldowns by 1 each turn (stacks with normal reduction)\n• {self.duration} turns remaining" 

class UnderwaterCursedShell(Item):
    def __init__(self):
        super().__init__(
            name="Underwater Cursed Shell",
            description="A mysterious shell that either heals or harms its target.",
            rarity="Rare",
            item_type="Consumable",
            icon_path="assets/items/underwater_cursed_shell.png",
            max_stack=5
        )
        self.cooldown = 15  # 15 turns cooldown
    
    def use(self, user: Character, target: Character) -> bool:
        """Randomly heal or damage the target."""
        # Call base class use method to log the use
        if not super().use(user, target):
            return False
        
        # 50/50 chance to heal or damage
        import random
        amount = 2250
        is_heal = random.random() < 0.5
        
        if is_heal:
            # Calculate healing amount with buffs
            heal_amount = amount
            for buff in target.buffs:
                if hasattr(buff, 'modify_healing_received'):
                    heal_amount = buff.modify_healing_received(heal_amount)
            
            # Heal the target
            target.heal(heal_amount)
            
            # Log the heal
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    f"The shell resonates with healing energy!",
                    GameEngine.instance.battle_log.TEXT_COLOR
                )
                GameEngine.instance.battle_log.add_message(
                    f"  {target.name} is healed for {heal_amount} HP",
                    GameEngine.instance.battle_log.HEAL_COLOR
                )
        else:
            # Deal damage
            target.take_damage(amount)
            
            # Log the damage
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    f"The shell unleashes a curse!",
                    GameEngine.instance.battle_log.TEXT_COLOR
                )
                GameEngine.instance.battle_log.add_message(
                    f"  {target.name} takes {amount} damage!",
                    GameEngine.instance.battle_log.DAMAGE_COLOR
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
        title_surface = title_font.render(self.name, True, self.RARITY_COLORS["Rare"])
        desc_surface = desc_font.render(self.description, True, (220, 220, 220))
        
        # Prepare effect text
        effect_lines = [
            "Effects:",
            "• 50% chance to heal target for 2250 HP",
            "• 50% chance to damage target for 2250",
            "• Cooldown: 15 turns",
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