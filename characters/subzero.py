from characters.base_character import Character, Stats, StatusEffect
from abilities.base_ability import Ability, AbilityEffect
from typing import List
import pygame
import types

def create_subzero():
    """Create Atlantean Sub Zero - A powerful ice mage that can be either a boss or playable character"""
    # Create character stats
    stats = Stats(
        max_hp=7000,
        current_hp=7000,
        max_mana=3000,
        current_mana=3000,
        attack=80,
        defense=15,
        speed=5
    )
    
    # Create the character
    subzero = Character("Atlantean Sub Zero", stats, "assets/characters/atlantean_subzero.png")
    
    # Create abilities
    
    # Iceball - High damage single target attack with chance to freeze
    iceball = Ability(
        name="Iceball",
        description="A devastating ball of ice that deals 600 damage with 10% chance to freeze the target for 2 turns",
        icon_path="assets/abilities/ice_blast.png",  # Reusing ice blast icon
        effects=[AbilityEffect("damage", 600)],  # Add damage effect
        cooldown=3,
        mana_cost=40
    )
    
    # Override use method to handle freeze chance
    def iceball_use(caster: Character, targets: List[Character]) -> bool:
        if not iceball.can_use(caster):
            return False
        
        if not targets:
            return False
            
        # Apply mana cost with buff modifications
        modified_mana_cost = iceball.mana_cost
        for buff in caster.buffs:
            if hasattr(buff, 'modify_mana_cost'):
                modified_mana_cost = buff.modify_mana_cost(modified_mana_cost)
        caster.stats.current_mana -= modified_mana_cost
        
        # Calculate base damage
        damage = iceball.effects[0].value
        
        # Apply damage increases from caster's buffs
        for buff in caster.buffs:
            if hasattr(buff, 'apply_damage_increase'):
                damage = buff.apply_damage_increase(damage)
        
        # Apply damage increases from target's debuffs
        for debuff in targets[0].debuffs:
            if hasattr(debuff, 'apply_damage_increase'):
                damage = debuff.apply_damage_increase(damage)
        
        # Deal the modified damage
        targets[0].take_damage(damage)
        
        # Call on_damage_dealt for buffs that need it
        for buff in caster.buffs:
            if hasattr(buff, 'on_damage_dealt'):
                buff.on_damage_dealt(damage)
        
        # 10% chance to freeze
        import random
        if random.random() < 0.10:  # 10% chance
            # Import IceCrystal for frozen image caching
            from modifiers.talent_modifiers import IceCrystal
            
            # Create freeze effect
            class FrozenDebuff:
                def __init__(self):
                    self.type = "custom"
                    self.value = 2  # Duration display
                    self.name = "Frozen"
                    self.description = "Frozen solid! Cannot use abilities"
                    self.duration = 2
                    self.heal_per_turn = 0
                    self.icon = iceball.icon
                    
                    # Store original image and create frozen version
                    self.original_image = targets[0].image
                    self.frozen_image = IceCrystal.get_frozen_image(self.original_image)
                    targets[0].image = self.frozen_image
                    
                    # Store original ability use functions and draw methods
                    self.original_abilities = []
                    
                    def create_draw_with_x(original_draw):
                        def draw_with_x(self_ability, screen):
                            # Call original draw if it exists
                            if original_draw:
                                original_draw(screen)
                            else:
                                # Default draw if no original draw method
                                screen.blit(self_ability.icon, self_ability.position)
                            
                            # Create a new surface for the X overlay
                            x_size = self_ability.icon.get_width()
                            x_surface = pygame.Surface((x_size, x_size), pygame.SRCALPHA)
                            x_color = (255, 0, 0, 180)  # Semi-transparent red
                            x_thickness = 4  # Thicker lines for better visibility
                            
                            # Draw the X with a black outline for better visibility
                            # Draw black outline
                            outline_color = (0, 0, 0, 180)
                            outline_thickness = x_thickness + 2
                            pygame.draw.line(x_surface, outline_color, (0, 0), (x_size, x_size), outline_thickness)
                            pygame.draw.line(x_surface, outline_color, (0, x_size), (x_size, 0), outline_thickness)
                            
                            # Draw red X
                            pygame.draw.line(x_surface, x_color, (0, 0), (x_size, x_size), x_thickness)
                            pygame.draw.line(x_surface, x_color, (0, x_size), (x_size, 0), x_thickness)
                            
                            # Draw the X overlay in a separate pass to ensure it's on top
                            screen.blit(x_surface, self_ability.position)
                        return draw_with_x
                    
                    # Override abilities
                    for ability in targets[0].abilities:
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
                    self.description = f"Frozen solid! Cannot use abilities\n{self.duration} turns remaining"
                    
                    if self.duration <= 0:
                        # Restore original image and abilities
                        targets[0].image = self.original_image
                        for ability, original_use, original_draw in self.original_abilities:
                            ability.use = original_use
                            if original_draw:
                                ability.draw = original_draw
                            else:
                                # Remove draw method if it didn't have one originally
                                delattr(ability, 'draw')
                        return False
                    return True
                    
                def get_tooltip_title(self):
                    return f"{self.name} ({self.duration} turns)"
                    
                def get_tooltip_text(self):
                    return self.description
            
            # Add the freeze debuff
            targets[0].add_buff(FrozenDebuff())
            
            # Log the freeze
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    f"{targets[0].name} has been frozen solid!",
                    GameEngine.instance.battle_log.BUFF_COLOR
                )
        
        # Start cooldown
        iceball.current_cooldown = iceball.cooldown
        return True
    
    iceball.use = iceball_use
    
    # Ice Wall - Defensive ability that reduces damage taken
    ice_wall = Ability(
        name="Ice Wall",
        description="Create a wall of ice that reduces damage taken by 50% for 3 turns",
        icon_path="assets/abilities/ice_wall.png",
        effects=[AbilityEffect("damage_reduction", 50, 3)],
        cooldown=5,
        mana_cost=60,
        auto_self_target=True
    )
    
    # Override ice wall use method to buff all allies
    def ice_wall_use(caster: Character, targets: List[Character]) -> bool:
        if not ice_wall.can_use(caster):
            return False
            
        # Deduct mana cost
        caster.stats.current_mana -= ice_wall.mana_cost
        
        # Get all allies
        from engine.game_engine import GameEngine
        if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
            stage = GameEngine.instance.stage_manager.current_stage
            # Get allies from stage_manager instead of stage
            allies = stage.bosses if caster in stage.bosses else GameEngine.instance.stage_manager.player_characters
            
            # Apply damage reduction buff to all allies
            for ally in allies:
                # Create the buff effect
                class IceWallBuff(StatusEffect):
                    def __init__(self):
                        super().__init__("ice_wall", 50, 3, ice_wall.icon)
                        self.name = "Ice Wall"
                        self._description = "Protected by a wall of ice\nDamage taken reduced by 50%"
                    
                    def update(self):
                        """Update the buff and return True if it should continue"""
                        self.duration -= 1
                        self._description = f"Protected by a wall of ice\nDamage taken reduced by 50%\n{self.duration} turns remaining"
                        return self.duration > 0
                    
                    def get_damage_reduction(self) -> float:
                        """Return the damage reduction percentage"""
                        return 50.0  # 50% damage reduction
                    
                    @property
                    def description(self) -> str:
                        """Override to prevent default description"""
                        return self._description
                    
                    @description.setter
                    def description(self, value: str):
                        self._description = value
                    
                    def get_tooltip_title(self) -> str:
                        return "Ice Wall"
                    
                    def get_tooltip_text(self) -> str:
                        effects = [
                            "Effects:",
                            "• Reduces all incoming damage by 50%",
                            "• Protects all allies with a wall of ice",
                            f"• {self.duration} turns remaining"
                        ]
                        return "\n".join(effects)
                
                # Add the buff
                ally.add_buff(IceWallBuff())
            
            # Log the buff
            GameEngine.instance.battle_log.add_message(
                f"{caster.name} surrounds the team with a wall of ice!",
                GameEngine.instance.battle_log.BUFF_COLOR
            )
        
        # Start cooldown
        ice_wall.current_cooldown = ice_wall.cooldown
        return True
    
    ice_wall.use = ice_wall_use
    
    # Absolute Zero - Massive damage and allows another action
    absolute_zero = Ability(
        name="Absolute Zero",
        description="A devastating attack that deals 1000 damage. This ability does not end Sub Zero's turn.",
        icon_path="assets/abilities/frost_nova.png",  # Reusing frost nova icon
        effects=[AbilityEffect("damage", 1000)],  # Add damage effect
        cooldown=15,
        mana_cost=100
    )
    
    # Override absolute zero use method
    def absolute_zero_use(caster: Character, targets: List[Character]) -> bool:
        if not absolute_zero.can_use(caster):
            return False
        
        if not targets:
            return False
            
        # Prevent self-targeting
        if targets[0] == caster:
            return False
            
        # Apply mana cost with buff modifications
        modified_mana_cost = absolute_zero.mana_cost
        for buff in caster.buffs:
            if hasattr(buff, 'modify_mana_cost'):
                modified_mana_cost = buff.modify_mana_cost(modified_mana_cost)
        caster.stats.current_mana -= modified_mana_cost
        
        # Calculate base damage
        damage = absolute_zero.effects[0].value
        
        # Apply damage increases from caster's buffs
        for buff in caster.buffs:
            if hasattr(buff, 'apply_damage_increase'):
                damage = buff.apply_damage_increase(damage)
        
        # Apply damage increases from target's debuffs
        for debuff in targets[0].debuffs:
            if hasattr(debuff, 'apply_damage_increase'):
                damage = debuff.apply_damage_increase(damage)
        
        # Deal the modified damage
        targets[0].take_damage(damage)
        
        # Call on_damage_dealt for buffs that need it
        for buff in caster.buffs:
            if hasattr(buff, 'on_damage_dealt'):
                buff.on_damage_dealt(damage)
        
        # Log the attack
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"{caster.name} unleashes Absolute Zero!",
                GameEngine.instance.battle_log.TEXT_COLOR
            )
            # Keep turn
            GameEngine.instance.game_state.is_player_turn = False
        
        # Start cooldown
        absolute_zero.current_cooldown = absolute_zero.cooldown
        return True
    
    absolute_zero.use = absolute_zero_use
    
    # Override heal method to reduce Absolute Zero cooldown
    original_heal = subzero.heal
    def heal_with_cooldown_reduction(amount: int) -> int:
        healed = original_heal(amount)
        if healed > 0 and absolute_zero.current_cooldown > 0:
            absolute_zero.current_cooldown = max(0, absolute_zero.current_cooldown - 1)
            # Log cooldown reduction
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    f"Absolute Zero cooldown reduced by 1 turn!",
                    GameEngine.instance.battle_log.BUFF_COLOR
                )
        return healed
    
    subzero.heal = heal_with_cooldown_reduction
    
    # Add abilities to character
    subzero.add_ability(iceball)
    subzero.add_ability(ice_wall)
    subzero.add_ability(absolute_zero)
    
    return subzero 