from characters.base_character import Character, Stats
from abilities.base_ability import Ability, AbilityEffect
from pathlib import Path
from typing import List
import random
import pygame

# Create a Piranha companion character class
class Piranha(Character):
    def __init__(self):
        stats = Stats(
            max_hp=550,
            current_hp=550,
            max_mana=0,  # No mana needed
            current_mana=0,
            attack=0,
            defense=0,
            speed=0
        )
        super().__init__("Piranha", stats, "assets/bosses/piranha.png")
        
        # Create Bite ability
        bite = Ability(
            name="Bite",
            description="A vicious bite that deals 200 damage",
            icon_path="assets/abilities/bite.png",
            effects=[AbilityEffect("damage", 200)],
            cooldown=0,
            mana_cost=0,
            can_self_target=False
        )
        self.add_ability(bite)

def create_shadowfin_boss():
    # Create Shadowfin boss stats
    stats = Stats(
        max_hp=9550,
        current_hp=9550,
        max_mana=4500,
        current_mana=4500,
        attack=20,
        defense=15,
        speed=12
    )
    
    # Create boss character
    shadowfin = Character("Shadowfin", stats, "assets/bosses/shadowfin.png")
    
    # Create abilities
    dark_bubble = Ability(
        name="Dark Bubble",
        description="Traps a target in a dark bubble, dealing 400 damage and restoring 45 mana",
        icon_path="assets/abilities/dark_bubble.png",
        effects=[
            AbilityEffect("damage", 400),
            AbilityEffect("restore_mana_self", 45)
        ],
        cooldown=0,
        mana_cost=80,
        can_self_target=False  # Cannot target self with damage ability
    )
    
    tidal_splash = Ability(
        name="Tidal Splash",
        description="Heals for 700 HP with a 20% chance to critically heal for 1400 HP",
        icon_path="assets/abilities/tidal_splash.png",
        effects=[],  # Remove the heal effect since we handle it in use method
        cooldown=10,
        mana_cost=100,
        auto_self_target=True  # Always targets self
    )
    
    # Override use method to handle crit chance
    def tidal_splash_use(caster: Character, targets: List[Character]) -> bool:
        if not tidal_splash.can_use(caster):
            return False
        
        # Apply mana cost
        caster.stats.current_mana -= tidal_splash.mana_cost
        
        # 20% chance to crit
        heal_amount = 1400 if random.random() < 0.2 else 700
        
        # Apply healing to caster (Shadowfin), not targets
        caster.heal(heal_amount)
        
        # Log the heal with crit information
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            message = f"{caster.name} uses {tidal_splash.name}!"
            GameEngine.instance.battle_log.add_message(message, GameEngine.instance.battle_log.TEXT_COLOR)
            
            crit_text = " (Critical Heal!)" if heal_amount == 1400 else ""
            heal_message = f"  Heals for {heal_amount}{crit_text}"
            GameEngine.instance.battle_log.add_message(heal_message, GameEngine.instance.battle_log.HEAL_COLOR)
        
        # Start cooldown
        tidal_splash.current_cooldown = tidal_splash.cooldown
        return True
    
    # Assign custom use method
    tidal_splash.use = tidal_splash_use
    
    # Custom tooltip method to show heal and crit chance
    def tidal_splash_tooltip(self, screen: pygame.Surface):
        if not self.is_hovered:
            return
            
        padding = 16
        line_spacing = 6
        
        # Prepare text surfaces with shadows
        title_shadow = self.tooltip_title_font.render(self.name, True, (0, 0, 0))
        title_surface = self.tooltip_title_font.render(self.name, True, self.TOOLTIP_TITLE_COLOR)
        desc_surface = self.tooltip_font.render(self.description, True, self.TOOLTIP_TEXT_COLOR)
        
        # Prepare heal text
        heal_text = "Heals for 700 HP"
        crit_text = "20% chance to critically heal for 1400 HP"
        heal_surface = self.tooltip_font.render(heal_text, True, self.TOOLTIP_HEAL_COLOR)
        crit_surface = self.tooltip_font.render(crit_text, True, self.TOOLTIP_HEAL_COLOR)
        
        # Calculate tooltip dimensions
        width = max(
            title_surface.get_width(),
            desc_surface.get_width(),
            heal_surface.get_width(),
            crit_surface.get_width()
        ) + padding * 3
        
        height = (padding * 2 + title_surface.get_height() + line_spacing +
                 desc_surface.get_height() + line_spacing * 2 +
                 heal_surface.get_height() + line_spacing +
                 crit_surface.get_height())
        
        # Add space for mana cost and cooldown
        if self.mana_cost > 0 or self.cooldown > 0:
            height += line_spacing + self.tooltip_detail_font.get_height()
        
        # Position tooltip to the right of the ability icon
        x = self.position[0] + self.icon.get_width() + 10
        y = self.position[1]
        
        # Keep tooltip on screen
        if x + width > screen.get_width():
            x = self.position[0] - width - 10
        if y + height > screen.get_height():
            y = screen.get_height() - height
        
        # Draw tooltip shadow
        shadow_rect = pygame.Rect(x + 4, y + 4, width, height)
        pygame.draw.rect(screen, self.TOOLTIP_SHADOW_COLOR, shadow_rect, border_radius=10)
        
        # Draw main tooltip background
        tooltip_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, self.TOOLTIP_BG_COLOR, tooltip_rect, border_radius=10)
        
        # Draw border with gradient effect
        border_rect = tooltip_rect.inflate(2, 2)
        pygame.draw.rect(screen, self.TOOLTIP_BORDER_COLOR, border_rect, width=2, border_radius=10)
        inner_border = tooltip_rect.inflate(-2, -2)
        pygame.draw.rect(screen, self.TOOLTIP_INNER_BORDER_COLOR, inner_border, width=1, border_radius=9)
        
        current_y = y + padding
        
        # Draw title with shadow
        screen.blit(title_shadow, (x + padding + 1, current_y + 1))
        screen.blit(title_surface, (x + padding, current_y))
        current_y += title_surface.get_height() + line_spacing
        
        # Draw separator line
        separator_y = current_y - line_spacing//2
        pygame.draw.line(screen, self.TOOLTIP_INNER_BORDER_COLOR,
                        (x + padding, separator_y),
                        (x + width - padding, separator_y))
        
        # Draw description
        screen.blit(desc_surface, (x + padding, current_y))
        current_y += desc_surface.get_height() + line_spacing * 2
        
        # Draw heal text with shadow
        heal_shadow = self.tooltip_font.render(heal_text, True, (0, 0, 0))
        screen.blit(heal_shadow, (x + padding + 1, current_y + 1))
        screen.blit(heal_surface, (x + padding, current_y))
        current_y += heal_surface.get_height() + line_spacing
        
        # Draw crit text with shadow
        crit_shadow = self.tooltip_font.render(crit_text, True, (0, 0, 0))
        screen.blit(crit_shadow, (x + padding + 1, current_y + 1))
        screen.blit(crit_surface, (x + padding, current_y))
        current_y += crit_surface.get_height() + line_spacing
        
        # Draw mana cost and cooldown
        if self.mana_cost > 0 or self.cooldown > 0:
            current_y += line_spacing
            pygame.draw.line(screen, self.TOOLTIP_INNER_BORDER_COLOR,
                           (x + padding, current_y - line_spacing//2),
                           (x + width - padding, current_y - line_spacing//2))
            
            if self.mana_cost > 0:
                mana_text = f"Mana Cost: {self.mana_cost}"
                mana_surface = self.tooltip_detail_font.render(mana_text, True, self.TOOLTIP_MANA_COLOR)
                screen.blit(mana_surface, (x + padding, current_y))
            
            if self.cooldown > 0:
                cooldown_text = f"Cooldown: {self.cooldown} turns"
                cooldown_surface = self.tooltip_detail_font.render(cooldown_text, True, self.TOOLTIP_TEXT_COLOR)
                if self.mana_cost > 0:
                    screen.blit(cooldown_surface, (x + width//2, current_y))
                else:
                    screen.blit(cooldown_surface, (x + padding, current_y))
    
    # Assign custom tooltip method
    tidal_splash.draw_tooltip = lambda screen: tidal_splash_tooltip(tidal_splash, screen)
    
    abyssal_empowerment = Ability(
        name="Abyssal Empowerment",
        description="Channel the power of the abyss to empower your abilities",
        icon_path="assets/abilities/abyssal_empowerment.png",
        effects=[],  # Custom effects handled in use method
        cooldown=12,
        mana_cost=100,
        auto_self_target=True  # Always targets self
    )
    
    # Override use method to handle the custom buff effects
    def abyssal_empowerment_use(caster: Character, targets: List[Character]) -> bool:
        if not abyssal_empowerment.can_use(caster):
            return False
        
        # Apply mana cost
        caster.stats.current_mana -= abyssal_empowerment.mana_cost
        
        # Create a custom buff that tracks both damage and healing increase
        class AbyssalBuff:
            def __init__(self):
                self.type = "custom"  # Custom type to handle special tooltip
                self.duration = 8
                self.damage_increase = 30
                self.healing_increase = 50
                self.icon = abyssal_empowerment.icon
                # Required attributes for all buffs
                self.value = self.damage_increase  # Show damage increase in buff display
                self.heal_per_turn = 0  # Not a healing over time buff
                self.name = "Abyssal Empowerment"  # For tooltip display
                self.description = f"Damage +30%, Healing +50%\n{self.duration} turns remaining"
            
            def apply_damage_increase(self, damage: int) -> int:
                return int(damage * (1 + self.damage_increase / 100))
            
            def apply_healing_increase(self, healing: int) -> int:
                return int(healing * (1 + self.healing_increase / 100))
            
            def update(self) -> bool:
                """Update the buff and return True if it should continue, False if it should be removed"""
                self.duration -= 1
                self.description = f"Damage +30%, Healing +50%\n{self.duration} turns remaining"
                return self.duration > 0  # Keep buff if duration is still positive
            
            def get_tooltip_text(self) -> str:
                """Return the text to show in the buff tooltip"""
                return f"Damage increased by {self.damage_increase}%\nHealing increased by {self.healing_increase}%\n{self.duration} turns remaining"
            
            def get_tooltip_title(self) -> str:
                """Return the title to show in the buff tooltip"""
                return "Abyssal Empowerment"
        
        # Add the buff to the caster (not targets)
        caster.buffs.append(AbyssalBuff())
        
        # Log the buff application
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            message = f"{caster.name} uses {abyssal_empowerment.name}!"
            GameEngine.instance.battle_log.add_message(message, GameEngine.instance.battle_log.TEXT_COLOR)
            
            buff_message = f"  Gains Abyssal Empowerment:"
            GameEngine.instance.battle_log.add_message(buff_message, GameEngine.instance.battle_log.BUFF_COLOR)
            
            damage_message = f"    • Damage increased by 30%"
            GameEngine.instance.battle_log.add_message(damage_message, GameEngine.instance.battle_log.DAMAGE_COLOR)
            
            heal_message = f"    • Healing increased by 50%"
            GameEngine.instance.battle_log.add_message(heal_message, GameEngine.instance.battle_log.HEAL_COLOR)
            
            duration_message = f"    • Lasts 8 turns"
            GameEngine.instance.battle_log.add_message(duration_message, GameEngine.instance.battle_log.TEXT_COLOR)
        
        # Start cooldown
        abyssal_empowerment.current_cooldown = abyssal_empowerment.cooldown
        return True
    
    # Custom tooltip method to show buff effects
    def abyssal_empowerment_tooltip(self, screen: pygame.Surface):
        if not self.is_hovered:
            return
            
        padding = 16
        line_spacing = 6
        
        # Prepare text surfaces with shadows
        title_shadow = self.tooltip_title_font.render(self.name, True, (0, 0, 0))
        title_surface = self.tooltip_title_font.render(self.name, True, self.TOOLTIP_TITLE_COLOR)
        desc_surface = self.tooltip_font.render(self.description, True, self.TOOLTIP_TEXT_COLOR)
        
        # Prepare buff text
        damage_text = "• Increases damage dealt by 30%"
        healing_text = "• Increases healing received by 50%"
        duration_text = "• Lasts 8 turns"
        
        damage_surface = self.tooltip_font.render(damage_text, True, self.TOOLTIP_DAMAGE_COLOR)
        healing_surface = self.tooltip_font.render(healing_text, True, self.TOOLTIP_HEAL_COLOR)
        duration_surface = self.tooltip_font.render(duration_text, True, self.TOOLTIP_TEXT_COLOR)
        
        # Calculate tooltip dimensions
        width = max(
            title_surface.get_width(),
            desc_surface.get_width(),
            damage_surface.get_width(),
            healing_surface.get_width(),
            duration_surface.get_width()
        ) + padding * 3
        
        # Calculate base height for content
        height = (padding * 2 +  # Top and bottom padding
                 title_surface.get_height() + line_spacing +  # Title
                 desc_surface.get_height() + line_spacing * 2 +  # Description
                 self.tooltip_font.get_height() + line_spacing +  # "Effects:" header
                 damage_surface.get_height() + line_spacing +  # Damage effect
                 healing_surface.get_height() + line_spacing +  # Healing effect
                 duration_surface.get_height() + line_spacing)  # Duration effect
        
        # Add space for mana cost and cooldown
        if self.mana_cost > 0 or self.cooldown > 0:
            height += line_spacing * 2 + self.tooltip_detail_font.get_height()  # Extra spacing for stats section
        
        # Position tooltip to the right of the ability icon
        x = self.position[0] + self.icon.get_width() + 10
        y = self.position[1]
        
        # Keep tooltip on screen
        if x + width > screen.get_width():
            x = self.position[0] - width - 10
        if y + height > screen.get_height():
            y = screen.get_height() - height
        
        # Draw tooltip shadow
        shadow_rect = pygame.Rect(x + 4, y + 4, width, height)
        pygame.draw.rect(screen, self.TOOLTIP_SHADOW_COLOR, shadow_rect, border_radius=10)
        
        # Draw main tooltip background
        tooltip_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, self.TOOLTIP_BG_COLOR, tooltip_rect, border_radius=10)
        
        # Draw border with gradient effect
        border_rect = tooltip_rect.inflate(2, 2)
        pygame.draw.rect(screen, self.TOOLTIP_BORDER_COLOR, border_rect, width=2, border_radius=10)
        inner_border = tooltip_rect.inflate(-2, -2)
        pygame.draw.rect(screen, self.TOOLTIP_INNER_BORDER_COLOR, inner_border, width=1, border_radius=9)
        
        current_y = y + padding
        
        # Draw title with shadow
        screen.blit(title_shadow, (x + padding + 1, current_y + 1))
        screen.blit(title_surface, (x + padding, current_y))
        current_y += title_surface.get_height() + line_spacing
        
        # Draw separator line
        separator_y = current_y - line_spacing//2
        pygame.draw.line(screen, self.TOOLTIP_INNER_BORDER_COLOR,
                        (x + padding, separator_y),
                        (x + width - padding, separator_y))
        
        # Draw description
        screen.blit(desc_surface, (x + padding, current_y))
        current_y += desc_surface.get_height() + line_spacing * 2
        
        # Draw effects header
        effects_text = "Effects:"
        effects_surface = self.tooltip_font.render(effects_text, True, self.TOOLTIP_TEXT_COLOR)
        screen.blit(effects_surface, (x + padding, current_y))
        current_y += effects_surface.get_height() + line_spacing
        
        # Draw damage text with shadow
        damage_shadow = self.tooltip_font.render(damage_text, True, (0, 0, 0))
        screen.blit(damage_shadow, (x + padding + 1, current_y + 1))
        screen.blit(damage_surface, (x + padding, current_y))
        current_y += damage_surface.get_height() + line_spacing
        
        # Draw healing text with shadow
        healing_shadow = self.tooltip_font.render(healing_text, True, (0, 0, 0))
        screen.blit(healing_shadow, (x + padding + 1, current_y + 1))
        screen.blit(healing_surface, (x + padding, current_y))
        current_y += healing_surface.get_height() + line_spacing
        
        # Draw duration text with shadow
        duration_shadow = self.tooltip_font.render(duration_text, True, (0, 0, 0))
        screen.blit(duration_shadow, (x + padding + 1, current_y + 1))
        screen.blit(duration_surface, (x + padding, current_y))
        current_y += duration_surface.get_height() + line_spacing
        
        # Draw mana cost and cooldown
        if self.mana_cost > 0 or self.cooldown > 0:
            current_y += line_spacing
            pygame.draw.line(screen, self.TOOLTIP_INNER_BORDER_COLOR,
                           (x + padding, current_y - line_spacing//2),
                           (x + width - padding, current_y - line_spacing//2))
            
            if self.mana_cost > 0:
                mana_text = f"Mana Cost: {self.mana_cost}"
                mana_surface = self.tooltip_detail_font.render(mana_text, True, self.TOOLTIP_MANA_COLOR)
                screen.blit(mana_surface, (x + padding, current_y))
            
            if self.cooldown > 0:
                cooldown_text = f"Cooldown: {self.cooldown} turns"
                cooldown_surface = self.tooltip_detail_font.render(cooldown_text, True, self.TOOLTIP_TEXT_COLOR)
                if self.mana_cost > 0:
                    screen.blit(cooldown_surface, (x + width//2, current_y))
                else:
                    screen.blit(cooldown_surface, (x + padding, current_y))
    
    # Assign custom methods
    abyssal_empowerment.use = abyssal_empowerment_use
    abyssal_empowerment.draw_tooltip = lambda screen: abyssal_empowerment_tooltip(abyssal_empowerment, screen)
    
    void_embrace = Ability(
        name="Void Embrace",
        description="Embrace the void to increase defense by 15 for 3 turns",
        icon_path="assets/abilities/void_embrace.png",
        effects=[AbilityEffect("buff", 15, duration=3)],
        cooldown=5,
        mana_cost=35,
        auto_self_target=True  # Always targets self
    )
    
    # Create a Piranha companion character class
    class Piranha(Character):
        def __init__(self):
            stats = Stats(
                max_hp=550,
                current_hp=550,
                max_mana=0,  # No mana needed
                current_mana=0,
                attack=0,
                defense=0,
                speed=0
            )
            super().__init__("Piranha", stats, "assets/bosses/piranha.png")
            
            # Create Bite ability
            bite = Ability(
                name="Bite",
                description="A vicious bite that deals 200 damage",
                icon_path="assets/abilities/bite.png",
                effects=[AbilityEffect("damage", 200)],
                cooldown=0,
                mana_cost=0,
                can_self_target=False
            )
            self.add_ability(bite)
    
    # Create Call Piranha ability
    call_piranha = Ability(
        name="Call Piranha",
        description="Summons a piranha with 550 HP that attacks with each of your abilities",
        icon_path="assets/abilities/call_piranha.png",
        effects=[],  # Custom effects handled in use method
        cooldown=7,  # Set cooldown to 7 turns
        mana_cost=0,
        auto_self_target=True
    )
    
    # Override use method to handle summoning
    def call_piranha_use(caster: Character, targets: List[Character]) -> bool:
        if not call_piranha.can_use(caster):
            return False
        
        # Create and add piranha to the stage
        from engine.game_engine import GameEngine
        from items.loot_table import LootTable
        from items.consumables import MurkyWaterVial, PiranhaTooth
        from items.buffs import PiranhaScales
        
        if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
            stage = GameEngine.instance.stage_manager.current_stage
            
            # Set up loot table for piranhas if not already set
            if not stage.get_loot_table(Piranha):
                piranha_loot = LootTable(min_total_drops=0, max_total_drops=3)  # 0-3 items total
                piranha_loot.add_entry(PiranhaTooth, 10.0, 0, 1)    # 10% chance for Piranha Tooth
                piranha_loot.add_entry(PiranhaScales, 30.0, 0, 1)   # 30% chance for Piranha Scales
                piranha_loot.add_entry(MurkyWaterVial, 60.0, 0, 1)  # 60% chance for Murky Water Vial
                stage.add_loot_table(Piranha, piranha_loot)
            
            # Create and add piranha
            piranha = Piranha()
            stage.bosses.append(piranha)
            
            # Log the summon
            GameEngine.instance.battle_log.add_message(
                f"{caster.name} uses {call_piranha.name}!",
                GameEngine.instance.battle_log.TEXT_COLOR
            )
            GameEngine.instance.battle_log.add_message(
                "  A vicious piranha appears!",
                GameEngine.instance.battle_log.TEXT_COLOR
            )
        
        # Start cooldown
        call_piranha.current_cooldown = call_piranha.cooldown
        return True
    
    # Override the use methods of other abilities to trigger piranha's bite
    def trigger_piranha_bite(caster: Character, targets: List[Character]):
        from engine.game_engine import GameEngine
        if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
            # Find the piranha in the stage's bosses
            for boss in GameEngine.instance.stage_manager.current_stage.bosses:
                if isinstance(boss, Piranha) and boss.is_alive():
                    # Use the piranha's bite ability three times
                    bite_ability = boss.abilities[0]
                    for i in range(3):  # Attack three times
                        if targets and not isinstance(targets[0], Piranha):  # Don't bite other piranhas
                            # Calculate base damage
                            base_damage = bite_ability.effects[0].value
                            
                            # Apply damage increases from piranha's buffs
                            for buff in boss.buffs:
                                if hasattr(buff, 'apply_damage_increase'):
                                    base_damage = buff.apply_damage_increase(base_damage)
                            
                            # Apply damage increases from target's debuffs
                            target = targets[0]
                            final_damage = base_damage
                            for debuff in target.debuffs:
                                if hasattr(debuff, 'apply_damage_increase'):
                                    final_damage = debuff.apply_damage_increase(final_damage)
                            
                            # Deal the damage
                            target.take_damage(final_damage)
                            
                            # Log the attack
                            if GameEngine.instance:
                                GameEngine.instance.battle_log.add_message(
                                    f"  Piranha bites {target.name} for {final_damage} damage!",
                                    GameEngine.instance.battle_log.DAMAGE_COLOR
                                )
    
    # Modify the use methods of other abilities to trigger piranha bite
    original_dark_bubble_use = dark_bubble.use
    def dark_bubble_with_bite_use(caster: Character, targets: List[Character]) -> bool:
        result = original_dark_bubble_use(caster, targets)
        if result:
            trigger_piranha_bite(caster, targets)
        return result
    dark_bubble.use = dark_bubble_with_bite_use
    
    original_tidal_splash_use = tidal_splash.use
    def tidal_splash_with_bite_use(caster: Character, targets: List[Character]) -> bool:
        result = original_tidal_splash_use(caster, targets)
        if result:
            trigger_piranha_bite(caster, targets)
        return result
    tidal_splash.use = tidal_splash_with_bite_use
    
    original_abyssal_empowerment_use = abyssal_empowerment.use
    def abyssal_empowerment_with_bite_use(caster: Character, targets: List[Character]) -> bool:
        result = original_abyssal_empowerment_use(caster, targets)
        if result:
            trigger_piranha_bite(caster, targets)
        return result
    abyssal_empowerment.use = abyssal_empowerment_with_bite_use
    
    # Assign custom use method to Call Piranha
    call_piranha.use = call_piranha_use
    
    # Add abilities
    shadowfin.add_ability(dark_bubble)
    shadowfin.add_ability(tidal_splash)
    shadowfin.add_ability(abyssal_empowerment)
    shadowfin.add_ability(call_piranha)
    
    return shadowfin 