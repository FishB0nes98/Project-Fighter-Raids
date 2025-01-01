from characters.base_character import Character, Stats
from abilities.base_ability import Ability, AbilityEffect, StatusEffect
from typing import List
import pygame
import types

class SunGodsProtectionBuff(StatusEffect):
    """Buff that increases damage reduction by 80%"""
    def __init__(self):
        super().__init__(
            type="damage_reduction",  # Keep damage_reduction type for functionality
            value=80,  # 80% damage reduction
            duration=5,  # 5 turns
            icon=pygame.image.load("assets/abilities/sun_protection.png")
        )
        self.name = "Sun God's Protection"
        self.description = "Protected by the Sun God - Reduces damage taken by 80%"
        self.is_removable = True  # Allow buff to be removed
        self.is_protection = True  # Mark as protection buff to not block abilities
    
    def get_tooltip_title(self) -> str:
        return "Sun God's Protection"
    
    def get_tooltip_text(self) -> str:
        return f"Reduces damage taken by {self.value}%\n{self.duration} turns remaining"
    
    def get_damage_reduction(self) -> float:
        """Return the damage reduction value for the base character to use"""
        return self.value

def create_atlantean_kotal_kahn():
    """Create Atlantean Kotal Kahn - A powerful Aztec warrior god"""
    # Create character stats
    stats = Stats(
        max_hp=8500,
        current_hp=8500,
        max_mana=2500,
        current_mana=2500,
        attack=85,
        defense=25,
        speed=4
    )
    
    # Create the character
    kotal = Character("Atlantean Kotal Kahn", stats, "assets/characters/atlantean_kotal_kahn.png")
    
    # Create Sunburst ability
    sunburst = Ability(
        name="Sunburst",
        description="Channel the power of the sun to heal allies for 400 HP and damage enemies for 400",
        icon_path="assets/abilities/sunburst.png",
        effects=[
            AbilityEffect("heal_all", 400),
            AbilityEffect("damage_all", 400)
        ],
        cooldown=5,
        mana_cost=90,
        auto_self_target=True  # Auto-target since it affects everyone
    )
    
    # Create SunGod's Protection ability
    sun_protection = Ability(
        name="SunGod's Protection",
        description="Call upon the Sun God's blessing to reduce damage taken by 80% for 5 turns",
        icon_path="assets/abilities/sun_protection.png",
        effects=[AbilityEffect("buff", 80)],
        cooldown=6,
        mana_cost=100,
        auto_self_target=True
    )
    
    def sun_protection_use(caster: Character, targets: List[Character]) -> bool:
        if not sun_protection.can_use(caster):
            return False
        
        # Deduct mana cost
        modified_mana_cost = sun_protection.mana_cost
        for buff in caster.buffs:
            if hasattr(buff, 'modify_mana_cost'):
                modified_mana_cost = buff.modify_mana_cost(modified_mana_cost)
        caster.stats.current_mana -= modified_mana_cost
        
        # Apply the protection buff
        protection_buff = SunGodsProtectionBuff()
        caster.add_buff(protection_buff)
        
        # Add battle log message
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"{caster.name} is blessed with the Sun God's protection!",
                GameEngine.instance.battle_log.BUFF_COLOR
            )
        
        # Start cooldown
        sun_protection.current_cooldown = sun_protection.cooldown
        return True
    
    sun_protection.use = sun_protection_use
    
    # Create Blood Sacrifice ability
    blood_sacrifice = Ability(
        name="Blood Sacrifice",
        description="Sacrifice 1000 HP to restore all mana",
        icon_path="assets/abilities/blood_sacrifice.png",
        effects=[AbilityEffect("self_damage", 1000)],
        cooldown=0,
        mana_cost=0,
        auto_self_target=True
    )
    
    def blood_sacrifice_use(caster: Character, targets: List[Character]) -> bool:
        # Check if caster has enough HP to sacrifice
        if caster.stats.current_hp <= 1000:
            return False
            
        # Deal damage to self
        caster.take_damage(1000)
        
        # Restore full mana
        mana_restored = caster.stats.max_mana - caster.stats.current_mana
        caster.stats.current_mana = caster.stats.max_mana
        
        # Reset Sunburst cooldown
        for ability in caster.abilities:
            if ability.name == "Sunburst":
                ability.current_cooldown = 0
        
        # Add battle log message
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"{caster.name} sacrifices 1000 HP to restore {mana_restored} mana and reset Sunburst's cooldown!",
                GameEngine.instance.battle_log.DAMAGE_COLOR
            )
        
        return True
    
    blood_sacrifice.use = blood_sacrifice_use
    
    # Override use method to handle healing and damage
    def sunburst_use(caster: Character, targets: List[Character]) -> bool:
        if not sunburst.can_use(caster) or caster.stats.current_mana < sunburst.mana_cost:
            return False
        
        # Deduct mana cost
        modified_mana_cost = sunburst.mana_cost
        for buff in caster.buffs:
            if hasattr(buff, 'modify_mana_cost'):
                modified_mana_cost = buff.modify_mana_cost(modified_mana_cost)
        caster.stats.current_mana -= modified_mana_cost
        
        from engine.game_engine import GameEngine
        if not GameEngine.instance or not GameEngine.instance.stage_manager.current_stage:
            return False
            
        # Get all allies (player characters)
        allies = [char for char in GameEngine.instance.stage_manager.player_characters 
                 if char.is_alive()]  # Removed is_targetable check for healing
        
        # Get all enemies (bosses)
        enemies = [boss for boss in GameEngine.instance.stage_manager.current_stage.bosses 
                  if boss.is_alive() and boss.is_targetable()]
        
        # Heal all allies
        heal_amount = sunburst.effects[0].value
        for ally in allies:
            actual_healing = ally.heal(heal_amount)
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    f"  {ally.name} is healed for {actual_healing} HP!",
                    GameEngine.instance.battle_log.HEAL_COLOR
                )
        
        # Calculate base damage
        base_damage = sunburst.effects[1].value
        
        # Apply damage increases from caster's buffs
        for buff in caster.buffs:
            if hasattr(buff, 'apply_damage_increase'):
                base_damage = buff.apply_damage_increase(base_damage)
        
        # Damage all enemies
        for enemy in enemies:
            # Calculate final damage including target's debuffs
            damage = base_damage
            for debuff in enemy.debuffs:
                if hasattr(debuff, 'apply_damage_increase'):
                    damage = debuff.apply_damage_increase(damage)
            
            # Deal the damage
            enemy.take_damage(damage)
            
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    f"  {enemy.name} takes {damage} damage from Sunburst!",
                    GameEngine.instance.battle_log.DAMAGE_COLOR
                )
        
        # Call on_damage_dealt for buffs that need it (with total damage dealt)
        total_damage = base_damage * len(enemies)
        for buff in caster.buffs:
            if hasattr(buff, 'on_damage_dealt'):
                buff.on_damage_dealt(total_damage)
        
        # Start cooldown
        sunburst.current_cooldown = sunburst.cooldown
        return True
    
    sunburst.use = sunburst_use
    
    # Create Dagger Throw ability
    dagger_throw = Ability(
        name="Dagger Throw",
        description="Throw a mystical dagger that deals 600 damage and stuns the target for 3 turns. Has 75% chance to bounce to other enemies.",
        icon_path="assets/abilities/dagger_throw.png",
        effects=[AbilityEffect("damage", 600)],
        cooldown=6,
        mana_cost=120,
        auto_self_target=False
    )
    
    def dagger_throw_use(caster: Character, targets: List[Character]) -> bool:
        if not dagger_throw.can_use(caster):
            return False
            
        # Get all enemies for potential bounce
        from engine.game_engine import GameEngine
        if not GameEngine.instance or not GameEngine.instance.stage_manager.current_stage:
            return False
            
        # Get all enemies (based on caster type)
        if isinstance(caster, type(GameEngine.instance.stage_manager.player_characters[0])):
            # Player casting, get all bosses
            all_enemies = [boss for boss in GameEngine.instance.stage_manager.current_stage.bosses 
                         if boss.is_alive() and boss.is_targetable()]
        else:
            # Boss casting, get all players
            all_enemies = [char for char in GameEngine.instance.stage_manager.player_characters 
                         if char.is_alive() and char.is_targetable()]
        
        # Deal damage and stun main target
        main_target = targets[0]
        main_target.take_damage(600)
        
        # Create and apply stun debuff
        class StunDebuff:
            def __init__(self, target, ability_icon):
                self.type = "custom"
                self.value = 3  # Duration display
                self.name = "Stunned"
                self.description = "Stunned! Cannot use abilities"
                self.duration = 3
                self.heal_per_turn = 0
                self.icon = ability_icon
                self.target = target  # Store target reference
                
                # Store original image and create stunned version
                self.original_image = target.image
                self.stunned_image = target.image.copy()
                self.stunned_image.fill((150, 150, 150), special_flags=pygame.BLEND_MULT)
                target.image = self.stunned_image
                
                # Store original ability use functions and draw methods
                self.original_abilities = []
                
                def create_draw_with_x(original_draw):
                    def draw_with_x(self_ability, screen):
                        # Call original draw if it exists
                        if original_draw:
                            original_draw(screen)
                        else:
                            screen.blit(self_ability.icon, self_ability.position)
                        
                        # Create X overlay
                        x_size = self_ability.icon.get_width()
                        x_surface = pygame.Surface((x_size, x_size), pygame.SRCALPHA)
                        x_color = (255, 0, 0, 180)
                        x_thickness = 4
                        
                        # Draw black outline
                        outline_color = (0, 0, 0, 180)
                        outline_thickness = x_thickness + 2
                        pygame.draw.line(x_surface, outline_color, (0, 0), (x_size, x_size), outline_thickness)
                        pygame.draw.line(x_surface, outline_color, (0, x_size), (x_size, 0), outline_thickness)
                        
                        # Draw red X
                        pygame.draw.line(x_surface, x_color, (0, 0), (x_size, x_size), x_thickness)
                        pygame.draw.line(x_surface, x_color, (0, x_size), (x_size, 0), x_thickness)
                        
                        screen.blit(x_surface, self_ability.position)
                    return draw_with_x
                
                # Override abilities
                for ability in target.abilities:
                    original_draw = ability.draw if hasattr(ability, 'draw') else None
                    original_use = ability.use
                    self.original_abilities.append((ability, original_use, original_draw))
                    
                    # Override use function to disable ability
                    ability.use = lambda *args, **kwargs: False
                    
                    # Create and bind the draw method
                    draw_with_x = create_draw_with_x(original_draw)
                    ability.draw = types.MethodType(draw_with_x, ability)
            
            def update(self):
                """Update the debuff and return True if it should continue"""
                self.duration -= 1
                self.description = f"Stunned! Cannot use abilities\n{self.duration} turns remaining"
                
                if self.duration <= 0:
                    # Restore original image and abilities
                    self.target.image = self.original_image
                    for ability, original_use, original_draw in self.original_abilities:
                        ability.use = original_use
                        if original_draw:
                            ability.draw = original_draw
                        else:
                            delattr(ability, 'draw')
                    return False
                return True
            
            def get_tooltip_title(self):
                return f"{self.name} ({self.duration} turns)"
            
            def get_tooltip_text(self):
                return self.description
        
        # Remove any existing stun debuff
        main_target.debuffs = [d for d in main_target.debuffs if not (hasattr(d, 'name') and d.name == "Stunned")]
        
        # Apply new stun debuff
        stun = StunDebuff(main_target, dagger_throw.icon)
        main_target.add_debuff(stun)
        
        # Log main target effects
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"Dagger Throw hits {main_target.name} for 600 damage!",
                GameEngine.instance.battle_log.DAMAGE_COLOR
            )
            GameEngine.instance.battle_log.add_message(
                f"{main_target.name} is stunned for 3 turns!",
                GameEngine.instance.battle_log.BUFF_COLOR
            )
        
        # Handle bounces to other enemies
        import random
        for enemy in all_enemies:
            if enemy != main_target and random.random() < 0.75:  # 75% bounce chance
                enemy.take_damage(600)
                
                # Apply stun to bounced target too
                enemy.debuffs = [d for d in enemy.debuffs if not (hasattr(d, 'name') and d.name == "Stunned")]
                stun = StunDebuff(enemy, dagger_throw.icon)
                enemy.add_debuff(stun)
                
                if GameEngine.instance:
                    GameEngine.instance.battle_log.add_message(
                        f"Dagger bounces to {enemy.name} for 600 damage and stuns them!",
                        GameEngine.instance.battle_log.DAMAGE_COLOR
                    )
        
        # Consume mana and start cooldown
        caster.stats.current_mana -= dagger_throw.mana_cost
        dagger_throw.current_cooldown = dagger_throw.cooldown
        
        # End turn
        if GameEngine.instance:
            GameEngine.instance.end_player_turn()
        
        return True
    
    dagger_throw.use = dagger_throw_use
    
    # Add abilities to Kotal Kahn
    kotal.add_ability(sunburst)
    kotal.add_ability(sun_protection)
    kotal.add_ability(blood_sacrifice)
    kotal.add_ability(dagger_throw)
    
    return kotal 