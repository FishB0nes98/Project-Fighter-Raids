from characters.base_character import Character, Stats
from abilities.base_ability import Ability, AbilityEffect
from characters.shadowfin_boss import Piranha
from pathlib import Path
from typing import List
import random
import pygame
import types

def create_atlantean_christie():
    """Create Atlantean Christie - A swift underwater fighter"""
    stats = Stats(
        max_hp=8000,
        current_hp=8000,
        max_mana=2000,
        current_mana=2000,
        attack=90,
        defense=20,
        speed=8
    )
    
    # Create the character
    christie = Character("Atlantean Christie", stats, "assets/characters/atlantean_christie.png")
    
    # Create Kick ability with multiple hits
    class MultiKickAbility(Ability):
        def __init__(self):
            super().__init__(
                name="Atlantean Kick",
                description="A powerful kick enhanced by water pressure that strikes 3 times. Final hit deals double damage!",
                icon_path="assets/abilities/kick.png",
                effects=[AbilityEffect("damage", 155)],  # Base damage for first two hits
                cooldown=3,
                mana_cost=90
            )
            self.hit_count = 0
            self.max_hits = 3
            self.hit_timer = 0
            self.hit_delay = 800  # 0.8 seconds in milliseconds
            self.is_executing = False
            self.current_targets = None
            self.caster = None
            self.last_update_time = 0  # Track last update time
            self.is_hovered = False  # Add this for tooltip handling
        
        def handle_mouse_motion(self, mouse_pos: tuple[int, int]):
            """Handle mouse motion for tooltip display"""
            ability_rect = pygame.Rect(self.position, (48, 48))  # Standard ability icon size
            self.is_hovered = ability_rect.collidepoint(mouse_pos)
        
        def use(self, caster: Character, targets: List[Character]) -> bool:
            if not self.can_use(caster):
                return False
            
            # Start the multi-hit sequence
            if not self.is_executing:
                # Only consume mana on first activation
                modified_mana_cost = self.mana_cost
                for buff in caster.buffs:
                    if hasattr(buff, 'modify_mana_cost'):
                        modified_mana_cost = buff.modify_mana_cost(modified_mana_cost)
                caster.stats.current_mana -= modified_mana_cost
                
                self.is_executing = True
                self.hit_count = 0
                self.hit_timer = pygame.time.get_ticks()
                self.last_update_time = self.hit_timer  # Initialize last update time
                self.current_targets = targets
                self.caster = caster
                
                # Execute first hit immediately
                self.execute_hit()
            
            # Don't end turn while executing
            return False
        
        def execute_hit(self):
            """Execute a single hit of the multi-hit sequence"""
            # Set damage based on hit number
            damage = 300 if self.hit_count == 2 else 155
            
            # Apply effects
            for target in self.current_targets:
                # Calculate base damage
                final_damage = damage
                
                # Apply damage increases from caster's buffs
                for buff in self.caster.buffs:
                    if hasattr(buff, 'apply_damage_increase'):
                        final_damage = buff.apply_damage_increase(final_damage)
                
                # Apply damage increases from target's debuffs
                for debuff in target.debuffs:
                    if hasattr(debuff, 'apply_damage_increase'):
                        final_damage = debuff.apply_damage_increase(final_damage)
                
                # Deal the modified damage
                target.take_damage(final_damage)
                
                # Call on_damage_dealt for buffs that need it
                for buff in self.caster.buffs:
                    if hasattr(buff, 'on_damage_dealt'):
                        buff.on_damage_dealt(final_damage)
                
                # Handle any healing effects from buffs or talents
                for buff in self.caster.buffs:
                    if hasattr(buff, 'on_hit_heal'):
                        heal_amount = buff.on_hit_heal(final_damage)
                        if heal_amount > 0:
                            self.caster.heal(heal_amount)
                
                # Handle any on-hit effects from buffs
                for buff in self.caster.buffs:
                    if hasattr(buff, 'on_hit_effect'):
                        buff.on_hit_effect(target)
                
                # Trigger piranha bite if present
                from engine.game_engine import GameEngine
                if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
                    # Check both player characters and bosses for piranhas
                    all_characters = (GameEngine.instance.stage_manager.player_characters + 
                                    GameEngine.instance.stage_manager.current_stage.bosses)
                    
                    # Find any piranha in either list
                    for character in all_characters:
                        if isinstance(character, Piranha) and character.is_alive():
                            # Use the piranha's bite ability
                            bite_ability = character.abilities[0]
                            # Calculate base damage
                            base_damage = bite_ability.effects[0].value
                            
                            # Apply damage increases from piranha's buffs
                            for buff in character.buffs:
                                if hasattr(buff, 'apply_damage_increase'):
                                    base_damage = buff.apply_damage_increase(base_damage)
                            
                            # Apply damage increases from target's debuffs
                            final_bite_damage = base_damage
                            for debuff in target.debuffs:
                                if hasattr(debuff, 'apply_damage_increase'):
                                    final_bite_damage = debuff.apply_damage_increase(final_bite_damage)
                            
                            # Deal the damage
                            target.take_damage(final_bite_damage)
                            
                            # Log the attack
                            if GameEngine.instance:
                                GameEngine.instance.battle_log.add_message(
                                    f"  Piranha bites {target.name} for {final_bite_damage} damage!",
                                    GameEngine.instance.battle_log.DAMAGE_COLOR
                                )
            
            # Log the hit
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                hit_number = self.hit_count + 1
                GameEngine.instance.battle_log.add_message(
                    f"Atlantean Kick - Hit {hit_number}: {damage} damage!",
                    GameEngine.instance.battle_log.DAMAGE_COLOR
                )
            
            self.hit_count += 1
            self.hit_timer = pygame.time.get_ticks()  # Reset timer for next hit
        
        def update(self):
            """Update the ability state"""
            # Don't update cooldown here - it's handled by GameEngine
            
            # Handle multi-hit sequence
            if self.is_executing:
                current_time = pygame.time.get_ticks()
                elapsed_time = current_time - self.hit_timer
                
                # Check if enough time has passed for next hit
                if elapsed_time >= self.hit_delay:
                    if self.hit_count < self.max_hits:
                        self.execute_hit()
                    else:
                        # Sequence complete
                        self.is_executing = False
                        self.hit_count = 0
                        self.current_cooldown = self.cooldown
                        # End turn after last hit
                        from engine.game_engine import GameEngine
                        if GameEngine.instance:
                            GameEngine.instance.end_player_turn()
    
    # Create Slamba Slam ability
    class SlambaSlam(Ability):
        def __init__(self):
            super().__init__(
                name="Slamba Slam",
                description="A powerful slam that deals 175 damage and stuns the target for 2 turns",
                icon_path="assets/abilities/samba_slam.png",
                effects=[AbilityEffect("damage", 175)],
                cooldown=5,
                mana_cost=40
            )
            # Initialize tooltip properties from base class
            self.tooltip_font = pygame.font.Font(None, 26)
            self.tooltip_title_font = pygame.font.Font(None, 32)
            self.tooltip_detail_font = pygame.font.Font(None, 24)
            self.position = (0, 0)
            self.is_hovered = False
        
        def handle_mouse_motion(self, mouse_pos: tuple[int, int]):
            """Handle mouse motion for tooltip display"""
            if hasattr(self, 'icon'):
                ability_rect = pygame.Rect(self.position, self.icon.get_size())
                self.is_hovered = ability_rect.collidepoint(mouse_pos)
        
        def use(self, caster: Character, targets: List[Character]) -> bool:
            if not self.can_use(caster):
                return False
            
            # Apply base damage and effects
            for target in targets:
                # Calculate base damage
                final_damage = self.effects[0].value
                
                # Apply damage increases from caster's buffs
                for buff in caster.buffs:
                    if hasattr(buff, 'apply_damage_increase'):
                        final_damage = buff.apply_damage_increase(final_damage)
                
                # Apply damage increases from target's debuffs
                for debuff in target.debuffs:
                    if hasattr(debuff, 'apply_damage_increase'):
                        final_damage = debuff.apply_damage_increase(final_damage)
                
                # Deal the modified damage
                target.take_damage(final_damage)
                
                # Call on_damage_dealt for buffs that need it
                for buff in caster.buffs:
                    if hasattr(buff, 'on_damage_dealt'):
                        buff.on_damage_dealt(final_damage)
                
                # Handle any healing effects from buffs or talents
                for buff in caster.buffs:
                    if hasattr(buff, 'on_hit_heal'):
                        heal_amount = buff.on_hit_heal(final_damage)
                        if heal_amount > 0:
                            caster.heal(heal_amount)
                
                # Apply stun debuff
                class StunDebuff:
                    def __init__(self, target, ability_icon):
                        self.type = "custom"  # Changed from "debuff" to "custom" to match working implementations
                        self.value = 2  # Duration display
                        self.name = "Stunned"
                        self.description = "Stunned! Cannot use abilities"
                        self.duration = 2
                        self.heal_per_turn = 0
                        # Use the same icon as the ability
                        self.icon = ability_icon
                        
                        # Store original image and create stunned version (visual feedback)
                        self.original_image = target.image
                        # Apply a slight gray tint to show stunned state
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
                            target.image = self.original_image
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
                        """Return the title to show in the buff tooltip"""
                        return f"{self.name} ({self.duration} turns)"
                    
                    def get_tooltip_text(self):
                        """Return the text to show in the buff tooltip"""
                        return self.description

                # Remove any existing stun debuff
                target.debuffs = [d for d in target.debuffs if not (hasattr(d, 'name') and d.name == "Stunned")]
                
                # Create StunDebuff with ability icon
                stun = StunDebuff(target, self.icon)
                target.add_debuff(stun)
                
                # Log the stun and damage
                from engine.game_engine import GameEngine
                if GameEngine.instance:
                    GameEngine.instance.battle_log.add_message(
                        f"Slamba Slam hits {target.name} for {final_damage} damage!",
                        GameEngine.instance.battle_log.DAMAGE_COLOR
                    )
                    GameEngine.instance.battle_log.add_message(
                        f"{target.name} is stunned for 2 turns!",
                        GameEngine.instance.battle_log.BUFF_COLOR
                    )
            
            # Consume mana
            modified_mana_cost = self.mana_cost
            for buff in caster.buffs:
                if hasattr(buff, 'modify_mana_cost'):
                    modified_mana_cost = buff.modify_mana_cost(modified_mana_cost)
            caster.stats.current_mana -= modified_mana_cost
            
            # Set cooldown
            self.current_cooldown = self.cooldown
            
            # End turn
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                GameEngine.instance.end_player_turn()
            
            return True
        
        def update(self):
            """Update the ability state"""
            # Don't update cooldown here - it's handled by GameEngine
            pass
    
    # Create and add the multi-hit kick ability
    kick = MultiKickAbility()
    christie.add_ability(kick)
    
    # Create and add the Slamba Slam ability
    slam = SlambaSlam()
    christie.add_ability(slam)
    
    # Create Charming Kiss ability
    class CharmingKiss(Ability):
        def __init__(self):
            super().__init__(
                name="Charming Kiss",
                description="A charming kiss that weakens the target's armor by 60% for 8 turns. Has a 25% chance to spread to other enemies.",
                icon_path="assets/abilities/charming_kiss.png",
                effects=[],  # No direct damage
                cooldown=16,
                mana_cost=120
            )
            self.is_hovered = False
            self.position = (0, 0)
        
        def handle_mouse_motion(self, mouse_pos: tuple[int, int]):
            """Handle mouse motion for tooltip display"""
            ability_rect = pygame.Rect(self.position, (48, 48))
            self.is_hovered = ability_rect.collidepoint(mouse_pos)
        
        def use(self, caster: Character, targets: List[Character]) -> bool:
            if not self.can_use(caster):
                return False
            
            # Get all potential targets (all enemies)
            from engine.game_engine import GameEngine
            if not GameEngine.instance or not GameEngine.instance.stage_manager.current_stage:
                return False
            
            # Get all enemies based on caster type
            if isinstance(caster, type(GameEngine.instance.stage_manager.player_characters[0])):
                # Player casting, get all bosses
                all_enemies = [boss for boss in GameEngine.instance.stage_manager.current_stage.bosses 
                             if boss.is_alive() and boss.is_targetable()]
            else:
                # Boss casting, get all players
                all_enemies = [char for char in GameEngine.instance.stage_manager.player_characters 
                             if char.is_alive() and char.is_targetable()]
            
            # Remove the main target from potential spread targets
            spread_targets = [enemy for enemy in all_enemies if enemy not in targets]
            
            def apply_charm_debuff(target):
                class ArmorReductionDebuff:
                    def __init__(self, icon):
                        self.type = "custom"
                        self.name = "Charmed"
                        self.description = "Armor reduced by 60%"
                        self.duration = 8
                        self.value = 60  # 60% reduction
                        self.icon = icon
                    
                    def update(self):
                        self.duration -= 1
                        return self.duration > 0
                    
                    def get_tooltip_title(self):
                        return f"{self.name} ({self.duration} turns)"
                    
                    def get_tooltip_text(self):
                        return self.description
                    
                    def apply_damage_increase(self, damage):
                        # Increase damage taken by 60%
                        return int(damage * 1.6)
                
                # Remove any existing Charmed debuff
                target.debuffs = [d for d in target.debuffs if not (hasattr(d, 'name') and d.name == "Charmed")]
                
                # Apply new debuff
                debuff = ArmorReductionDebuff(self.icon)
                target.add_debuff(debuff)
                
                # Log the effect
                if GameEngine.instance:
                    GameEngine.instance.battle_log.add_message(
                        f"Charming Kiss weakens {target.name}'s armor by 60%!",
                        GameEngine.instance.battle_log.BUFF_COLOR
                    )
            
            # Apply to main target(s)
            for target in targets:
                apply_charm_debuff(target)
            
            # 25% chance to spread to each additional enemy
            import random
            for target in spread_targets:
                if random.random() < 0.25:  # 25% chance
                    apply_charm_debuff(target)
                    if GameEngine.instance:
                        GameEngine.instance.battle_log.add_message(
                            f"Charming Kiss spreads to {target.name}!",
                            GameEngine.instance.battle_log.BUFF_COLOR
                        )
            
            # Consume mana
            modified_mana_cost = self.mana_cost
            for buff in caster.buffs:
                if hasattr(buff, 'modify_mana_cost'):
                    modified_mana_cost = buff.modify_mana_cost(modified_mana_cost)
            caster.stats.current_mana -= modified_mana_cost
            
            # Set cooldown
            self.current_cooldown = self.cooldown
            
            # End turn
            if GameEngine.instance:
                GameEngine.instance.end_player_turn()
            
            return True
        
        def update(self):
            pass
    
    # Create and add the Charming Kiss ability
    kiss = CharmingKiss()
    christie.add_ability(kiss)
    
    # Create Throwkick ability
    class Throwkick(Ability):
        def __init__(self):
            super().__init__(
                name="Throwkick",
                description="A devastating kick that deals 1000 damage and throws the target into other enemies, dealing 25% of target's max HP as splash damage",
                icon_path="assets/abilities/throwkick.png",
                effects=[AbilityEffect("damage", 1000)],
                cooldown=22,
                mana_cost=120
            )
            self.is_hovered = False
            self.position = (0, 0)
            # Set initial cooldown to 10
            self.current_cooldown = 10
        
        def handle_mouse_motion(self, mouse_pos: tuple[int, int]):
            """Handle mouse motion for tooltip display"""
            ability_rect = pygame.Rect(self.position, (48, 48))
            self.is_hovered = ability_rect.collidepoint(mouse_pos)
        
        def use(self, caster: Character, targets: List[Character]) -> bool:
            if not self.can_use(caster):
                return False
            
            # Get all enemies for splash damage
            from engine.game_engine import GameEngine
            if not GameEngine.instance or not GameEngine.instance.stage_manager.current_stage:
                return False
            
            # Get all enemies based on caster type
            if isinstance(caster, type(GameEngine.instance.stage_manager.player_characters[0])):
                # Player casting, get all bosses
                all_enemies = [boss for boss in GameEngine.instance.stage_manager.current_stage.bosses 
                             if boss.is_alive() and boss.is_targetable()]
            else:
                # Boss casting, get all players
                all_enemies = [char for char in GameEngine.instance.stage_manager.player_characters 
                             if char.is_alive() and char.is_targetable()]
            
            # Deal initial damage to main target
            main_target = targets[0]  # Get the first target
            
            # Calculate base damage
            final_damage = self.effects[0].value
            
            # Apply damage increases from caster's buffs
            for buff in caster.buffs:
                if hasattr(buff, 'apply_damage_increase'):
                    final_damage = buff.apply_damage_increase(final_damage)
            
            # Apply damage increases from target's debuffs
            for debuff in main_target.debuffs:
                if hasattr(debuff, 'apply_damage_increase'):
                    final_damage = debuff.apply_damage_increase(final_damage)
            
            # Deal the direct damage
            main_target.take_damage(final_damage)
            
            # Log the main damage
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    f"Throwkick hits {main_target.name} for {final_damage} damage!",
                    GameEngine.instance.battle_log.DAMAGE_COLOR
                )
            
            # Calculate splash damage (25% of target's max HP)
            splash_damage = int(main_target.stats.max_hp * 0.25)
            
            # Deal splash damage to all enemies (excluding the main target)
            for target in all_enemies:
                if target == main_target:  # Skip the main target for splash damage
                    continue
                    
                # Calculate final splash damage including target's debuffs
                final_splash = splash_damage
                for debuff in target.debuffs:
                    if hasattr(debuff, 'apply_damage_increase'):
                        final_splash = debuff.apply_damage_increase(final_splash)
                
                # Deal the splash damage
                target.take_damage(final_splash)
                
                # Log splash damage
                if GameEngine.instance:
                    GameEngine.instance.battle_log.add_message(
                        f"{main_target.name} crashes into {target.name} for {final_splash} splash damage!",
                        GameEngine.instance.battle_log.DAMAGE_COLOR
                    )
            
            # Call on_damage_dealt for buffs that need it (with total damage)
            total_damage = final_damage + (splash_damage * len(all_enemies))
            for buff in caster.buffs:
                if hasattr(buff, 'on_damage_dealt'):
                    buff.on_damage_dealt(total_damage)
            
            # Consume mana
            modified_mana_cost = self.mana_cost
            for buff in caster.buffs:
                if hasattr(buff, 'modify_mana_cost'):
                    modified_mana_cost = buff.modify_mana_cost(modified_mana_cost)
            caster.stats.current_mana -= modified_mana_cost
            
            # Set cooldown
            self.current_cooldown = self.cooldown
            
            # End turn
            if GameEngine.instance:
                GameEngine.instance.end_player_turn()
            
            return True
        
        def update(self):
            pass
    
    # Create and add the Throwkick ability
    throwkick = Throwkick()
    christie.add_ability(throwkick)
    
    # Set initial positions for ability tooltips
    ability_spacing = 60  # Pixels between abilities
    for i, ability in enumerate(christie.abilities):
        ability.position = (10 + i * ability_spacing, 10)  # Adjust these values as needed
    
    return christie 