from characters.base_character import Character, Stats
from abilities.base_ability import Ability, AbilityEffect
from typing import List
import pygame

class DarkTimeBombDebuff:
    """A ticking time bomb that explodes after 3 turns"""
    def __init__(self, target):
        self.type = "custom"
        self.name = "Dark Time Bomb"
        self.description = "A dark time bomb that will explode in 3 turns"
        self.duration = 3
        self.heal_per_turn = 0
        self.icon = pygame.image.load("assets/abilities/dark_time_bomb.png")
        self.target = target
        
    def update(self):
        """Update the debuff and return True if it should continue"""
        self.duration -= 1
        self.description = f"A dark time bomb that will explode in {self.duration} turns"
        
        if self.duration <= 0:
            # Explode!
            self.target.take_damage(885)
            # Log the explosion
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    f"Dark Time Bomb explodes on {self.target.name} for 885 damage!",
                    GameEngine.instance.battle_log.DAMAGE_COLOR
                )
            return False
        return True
        
    def get_tooltip_title(self):
        return f"{self.name} ({self.duration} turns)"
        
    def get_tooltip_text(self):
        return self.description

def create_atlantean_zasalamel():
    """Create Atlantean Zasalamel - A powerful shadow warrior"""
    # Create character stats
    stats = Stats(
        max_hp=29855,  # Buffed HP
        current_hp=29855,
        max_mana=6666,  # Buffed mana
        current_mana=6666,
        attack=100,
        defense=20,
        speed=8
    )
    
    # Create the character
    zasalamel = Character("Atlantean Zasalamel", stats, "assets/characters/atlantean_zasalamel.png")
    
    # Create Slash ability - AOE damage to all enemies
    slash = Ability(
        name="Slash",
        description="A powerful slash that deals 500 damage to all enemies",
        icon_path="assets/abilities/slash.png",
        effects=[AbilityEffect("damage_all", 500)],  # AOE damage
        cooldown=0,  # No cooldown
        mana_cost=0,  # No mana cost
        auto_self_target=True  # Make it auto-target since it's AOE
    )
    
    # Override use method to handle AOE damage
    def slash_use(caster: Character, targets: List[Character]) -> bool:
        if not slash.can_use(caster):
            return False
            
        # Apply mana cost
        caster.stats.current_mana -= slash.mana_cost
        
        # Get all enemies
        from engine.game_engine import GameEngine
        if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
            stage = GameEngine.instance.stage_manager.current_stage
            # Get enemies (player characters if caster is boss, bosses if caster is player)
            enemies = GameEngine.instance.stage_manager.player_characters if caster in stage.bosses else stage.bosses
            
            # Deal damage to all enemies
            base_damage = slash.effects[0].value
            
            # Apply damage increases from caster's buffs
            for buff in caster.buffs:
                if hasattr(buff, 'apply_damage_increase'):
                    base_damage = buff.apply_damage_increase(base_damage)
            
            # Deal damage to each enemy, considering their individual buffs/debuffs
            for enemy in enemies:
                if enemy.is_alive():
                    # Calculate final damage including target's debuffs
                    final_damage = base_damage
                    for debuff in enemy.debuffs:
                        if hasattr(debuff, 'apply_damage_increase'):
                            final_damage = debuff.apply_damage_increase(final_damage)
                    
                    # Deal the damage (damage reduction will be handled by take_damage)
                    enemy.take_damage(final_damage)
            
            # Log the attack
            GameEngine.instance.battle_log.add_message(
                f"{caster.name} unleashes a devastating slash!",
                GameEngine.instance.battle_log.TEXT_COLOR
            )
        
        # Start cooldown
        slash.current_cooldown = slash.cooldown
        return True
    
    slash.use = slash_use
    
    # Create Dark Time Bomb ability
    dark_time_bomb = Ability(
        name="Dark Time Bomb",
        description="Places a dark time bomb on two random enemies that explodes after 3 turns, dealing 885 damage",
        icon_path="assets/abilities/dark_time_bomb.png",
        effects=[],  # Custom handling in use method
        cooldown=10,
        mana_cost=100,
        auto_self_target=True
    )
    
    def dark_time_bomb_use(caster: Character, targets: List[Character]) -> bool:
        if not dark_time_bomb.can_use(caster):
            return False
            
        # Apply mana cost
        caster.stats.current_mana -= dark_time_bomb.mana_cost
        
        # Get all enemies
        from engine.game_engine import GameEngine
        if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
            stage = GameEngine.instance.stage_manager.current_stage
            enemies = GameEngine.instance.stage_manager.player_characters if caster in stage.bosses else stage.bosses
            
            # Get alive enemies
            valid_targets = [enemy for enemy in enemies if enemy.is_alive()]
            if len(valid_targets) > 0:
                # Choose up to 2 random targets
                import random
                num_targets = min(2, len(valid_targets))
                chosen_targets = random.sample(valid_targets, num_targets)
                
                # Apply the time bomb debuff to each target
                for target in chosen_targets:
                    target.add_debuff(DarkTimeBombDebuff(target))
                    
                    # Log the application
                    GameEngine.instance.battle_log.add_message(
                        f"{caster.name} plants a Dark Time Bomb on {target.name}!",
                        GameEngine.instance.battle_log.TEXT_COLOR
                    )
        
        # Start cooldown
        dark_time_bomb.current_cooldown = dark_time_bomb.cooldown
        return True
    
    dark_time_bomb.use = dark_time_bomb_use
    
    # Create Time Manipulation ability
    time_manipulation = Ability(
        name="Time Manipulation",
        description="Decrease allies' cooldowns by 2 and increase enemies' cooldowns by 2",
        icon_path="assets/abilities/time_manipulation.png",
        effects=[],  # Custom handling in use method
        cooldown=8,
        mana_cost=80,
        auto_self_target=True
    )
    
    def time_manipulation_use(caster: Character, targets: List[Character]) -> bool:
        if not time_manipulation.can_use(caster):
            return False
            
        # Apply mana cost
        caster.stats.current_mana -= time_manipulation.mana_cost
        
        # Get all characters
        from engine.game_engine import GameEngine
        if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
            stage = GameEngine.instance.stage_manager.current_stage
            
            # Get allies and enemies
            allies = stage.bosses if caster in stage.bosses else GameEngine.instance.stage_manager.player_characters
            enemies = GameEngine.instance.stage_manager.player_characters if caster in stage.bosses else stage.bosses
            
            # Decrease allies' cooldowns
            for ally in allies:
                if ally.is_alive():
                    for ability in ally.abilities:
                        if ability.current_cooldown > 0:  # Only affect abilities on cooldown
                            old_cooldown = ability.current_cooldown
                            ability.current_cooldown = max(0, ability.current_cooldown - 2)
                            if old_cooldown != ability.current_cooldown:
                                GameEngine.instance.battle_log.add_message(
                                    f"  {ally.name}'s {ability.name} cooldown reduced by {old_cooldown - ability.current_cooldown} turns!",
                                    GameEngine.instance.battle_log.BUFF_COLOR
                                )
            
            # Increase enemies' cooldowns
            for enemy in enemies:
                if enemy.is_alive():
                    for ability in enemy.abilities:
                        if ability.current_cooldown > 0:  # Only affect abilities on cooldown
                            old_cooldown = ability.current_cooldown
                            ability.current_cooldown = min(ability.cooldown, ability.current_cooldown + 2)
                            if old_cooldown != ability.current_cooldown:
                                GameEngine.instance.battle_log.add_message(
                                    f"  {enemy.name}'s {ability.name} cooldown increased by {ability.current_cooldown - old_cooldown} turns!",
                                    GameEngine.instance.battle_log.DAMAGE_COLOR
                                )
            
            # Main log message
            GameEngine.instance.battle_log.add_message(
                f"{caster.name} manipulates time!",
                GameEngine.instance.battle_log.TEXT_COLOR
            )
            
            # Don't end turn
            GameEngine.instance.game_state.is_player_turn = False
        
        # Start cooldown
        time_manipulation.current_cooldown = time_manipulation.cooldown
        return True
    
    time_manipulation.use = time_manipulation_use
    
    # Create Time Explosion ability
    time_explosion = Ability(
        name="Time Explosion",
        description="Deal 455 damage per ability on cooldown to all enemies (max 4 abilities per target)",
        icon_path="assets/abilities/time_explosion.png",
        effects=[],  # Custom handling in use method
        cooldown=12,
        mana_cost=120,
        auto_self_target=True
    )
    # Set initial cooldown to 5 turns
    time_explosion.current_cooldown = 5
    
    def time_explosion_use(caster: Character, targets: List[Character]) -> bool:
        if not time_explosion.can_use(caster):
            return False
            
        # Apply mana cost
        caster.stats.current_mana -= time_explosion.mana_cost
        
        # Get all enemies
        from engine.game_engine import GameEngine
        if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
            stage = GameEngine.instance.stage_manager.current_stage
            enemies = GameEngine.instance.stage_manager.player_characters if caster in stage.bosses else stage.bosses
            
            # Deal damage to each enemy based on their abilities on cooldown
            for enemy in enemies:
                if enemy.is_alive():
                    # Count abilities on cooldown (max 4)
                    abilities_on_cooldown = sum(1 for ability in enemy.abilities if ability.current_cooldown > 0)
                    abilities_on_cooldown = min(abilities_on_cooldown, 4)  # Cap at 4 abilities
                    
                    if abilities_on_cooldown > 0:
                        # Calculate damage
                        damage = 455 * abilities_on_cooldown
                        
                        # Apply damage increases from caster's buffs
                        for buff in caster.buffs:
                            if hasattr(buff, 'apply_damage_increase'):
                                damage = buff.apply_damage_increase(damage)
                        
                        # Apply damage increases from target's debuffs
                        for debuff in enemy.debuffs:
                            if hasattr(debuff, 'apply_damage_increase'):
                                damage = debuff.apply_damage_increase(damage)
                        
                        # Deal the damage
                        enemy.take_damage(damage)
                        
                        # Log the damage
                        GameEngine.instance.battle_log.add_message(
                            f"  Time Explosion hits {enemy.name} for {damage} damage! ({abilities_on_cooldown} abilities on cooldown)",
                            GameEngine.instance.battle_log.DAMAGE_COLOR
                        )
            
            # Main log message
            GameEngine.instance.battle_log.add_message(
                f"{caster.name} unleashes a Time Explosion!",
                GameEngine.instance.battle_log.TEXT_COLOR
            )
        
        # Start cooldown
        time_explosion.current_cooldown = time_explosion.cooldown
        return True
    
    time_explosion.use = time_explosion_use
    
    # Add abilities to Zasalamel
    zasalamel.add_ability(slash)
    zasalamel.add_ability(dark_time_bomb)
    zasalamel.add_ability(time_manipulation)
    zasalamel.add_ability(time_explosion)
    
    return zasalamel 