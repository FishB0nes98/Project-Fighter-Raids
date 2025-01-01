from characters.base_character import Character, Stats
from abilities.base_ability import Ability, AbilityEffect
from pathlib import Path
from typing import List

def create_atlantean_kagome():
    # Create Kagome's stats
    stats = Stats(
        max_hp=6170,
        current_hp=6170,
        max_mana=2620,
        current_mana=2620,
        attack=20,
        defense=15,
        speed=12
    )
    
    # Create Kagome character
    kagome = Character("Atlantean Kagome", stats, "assets/characters/kagome.png")
    
    # Create Kagome's abilities
    golden_arrow = Ability(
        name="Golden Arrow",
        description="A sacred arrow imbued with divine power that deals 345 damage",
        icon_path="assets/abilities/golden_arrow.png",
        effects=[AbilityEffect("damage", 345)],
        cooldown=0,
        mana_cost=0,
        can_self_target=False  # Cannot target self with damage ability
    )
    
    # Override use method to add visual effect
    def golden_arrow_use(caster: Character, targets: List[Character]) -> bool:
        if not golden_arrow.can_use(caster):
            return False
            
        # Apply mana cost
        caster.stats.current_mana -= golden_arrow.mana_cost
        
        # Create arrow effect
        from engine.game_engine import GameEngine
        if GameEngine.instance and targets:
            print("Creating Golden Arrow visual effect...")  # Debug print
            
            # Calculate arrow start position (center of caster)
            start_x = caster.position[0] + caster.image.get_width() // 2
            start_y = caster.position[1] + caster.image.get_height() // 2
            
            # Calculate arrow end position (center of target)
            target = targets[0]
            end_x = target.position[0] + target.image.get_width() // 2
            end_y = target.position[1] + target.image.get_height() // 2
            
            print(f"Arrow path: ({start_x}, {start_y}) -> ({end_x}, {end_y})")  # Debug print
            
            # Create and add the projectile effect
            arrow = GameEngine.instance.visual_effects.create_projectile(
                start_pos=(start_x, start_y),
                end_pos=(end_x, end_y),
                color=(255, 215, 0),  # Golden color
                duration=1.0,  # Increased to 1 second duration
                size=20,  # Doubled size
                trail_length=12  # Increased trail length
            )
            GameEngine.instance.visual_effects.add_effect(arrow)
            print("Added arrow effect to visual effects manager")  # Debug print
        else:
            print("Warning: GameEngine.instance or targets not available")  # Debug print

        # Apply effects to targets
        for target in targets:
            for effect in golden_arrow.effects:
                if effect.type == "damage":
                    # Get base damage
                    damage = effect.value
                    # Apply damage increase from caster's buffs
                    for buff in caster.buffs:
                        if hasattr(buff, 'apply_damage_increase'):
                            damage = buff.apply_damage_increase(damage)
                    target.take_damage(damage)
        
        # Start cooldown
        golden_arrow.current_cooldown = golden_arrow.cooldown
        return True
    
    # Assign custom use method
    golden_arrow.use = golden_arrow_use
    
    golden_arrow_storm = Ability(
        name="Golden Arrow Storm",
        description="Unleashes a barrage of sacred arrows that deal 300 damage to all enemies",
        icon_path="assets/abilities/golden_arrow_storm.png",
        effects=[AbilityEffect("damage_all", 300)],
        cooldown=3,
        mana_cost=80,
        auto_self_target=True  # Make it auto-target since it's AoE
    )
    
    # Override use method to handle AOE damage
    def golden_arrow_storm_use(caster: Character, targets: List[Character]) -> bool:
        if not golden_arrow_storm.can_use(caster):
            return False
        
        # Get all enemies
        from engine.game_engine import GameEngine
        if not GameEngine.instance or not GameEngine.instance.stage_manager.current_stage:
            return False
            
        # Get appropriate targets based on caster type
        if isinstance(caster, type(GameEngine.instance.stage_manager.player_characters[0])):
            # Player casting, target all bosses
            targets = [boss for boss in GameEngine.instance.stage_manager.current_stage.bosses 
                      if boss.is_alive() and boss.is_targetable()]
        else:
            # Boss casting, target all players
            targets = [char for char in GameEngine.instance.stage_manager.player_characters 
                      if char.is_alive() and char.is_targetable()]
        
        if not targets:
            return False
            
        # Apply mana cost with buff modifications
        modified_mana_cost = golden_arrow_storm.mana_cost
        for buff in caster.buffs:
            if hasattr(buff, 'modify_mana_cost'):
                modified_mana_cost = buff.modify_mana_cost(modified_mana_cost)
        caster.stats.current_mana -= modified_mana_cost
        
        # Calculate base damage
        base_damage = golden_arrow_storm.effects[0].value
        
        # Apply damage increases from caster's buffs
        for buff in caster.buffs:
            if hasattr(buff, 'apply_damage_increase'):
                base_damage = buff.apply_damage_increase(base_damage)
        
        # Deal damage to all targets
        for target in targets:
            # Calculate final damage including target's debuffs
            damage = base_damage
            for debuff in target.debuffs:
                if hasattr(debuff, 'apply_damage_increase'):
                    damage = debuff.apply_damage_increase(damage)
            
            # Deal the damage
            target.take_damage(damage)
            
            # Create arrow effect for each target
            if GameEngine.instance:
                # Calculate arrow start position (center of caster)
                start_x = caster.position[0] + caster.image.get_width() // 2
                start_y = caster.position[1] + caster.image.get_height() // 2
                
                # Calculate arrow end position (center of target)
                end_x = target.position[0] + target.image.get_width() // 2
                end_y = target.position[1] + target.image.get_height() // 2
                
                # Create and add the projectile effect
                arrow = GameEngine.instance.visual_effects.create_projectile(
                    start_pos=(start_x, start_y),
                    end_pos=(end_x, end_y),
                    color=(255, 215, 0),  # Golden color
                    duration=0.8,  # Slightly faster than single arrow
                    size=15,  # Slightly smaller than single arrow
                    trail_length=10
                )
                GameEngine.instance.visual_effects.add_effect(arrow)
        
        # Call on_damage_dealt for buffs that need it (with total damage dealt)
        total_damage = base_damage * len(targets)
        for buff in caster.buffs:
            if hasattr(buff, 'on_damage_dealt'):
                buff.on_damage_dealt(total_damage)
        
        # Start cooldown
        golden_arrow_storm.current_cooldown = golden_arrow_storm.cooldown
        return True
    
    golden_arrow_storm.use = golden_arrow_storm_use
    
    spiritwalk = Ability(
        name="Spiritwalk",
        description="Enter a spiritual state that reduces incoming damage by 90% and heals 500 HP per turn",
        icon_path="assets/abilities/spiritwalk.png",
        effects=[
            AbilityEffect("damage_reduction", 90, duration=3),  # 90% damage reduction
            AbilityEffect("heal_over_time", 500, duration=3),   # 500 HP heal per turn
        ],
        cooldown=12,
        mana_cost=120,
        auto_self_target=True,  # Make it auto-target self
        can_self_target=True    # Can be manually self-targeted too
    )
    
    ghostly_scream = Ability(
        name="Ghostly Scream",
        description="A piercing scream that deals 655 damage to all enemies and removes their buffs and debuffs",
        icon_path="assets/abilities/ghostly_scream.png",
        effects=[
            AbilityEffect("damage_all", 655),
            AbilityEffect("remove_effects", 0)  # Value doesn't matter for remove_effects
        ],
        cooldown=20,
        mana_cost=120,
        auto_self_target=True  # Make it auto-target since it's AoE
    )
    
    # Override use method to handle AOE damage and effect removal
    def ghostly_scream_use(caster: Character, targets: List[Character]) -> bool:
        if not ghostly_scream.can_use(caster):
            return False
        
        # Get all enemies
        from engine.game_engine import GameEngine
        if not GameEngine.instance or not GameEngine.instance.stage_manager.current_stage:
            return False
            
        # Get appropriate targets based on caster type
        if isinstance(caster, type(GameEngine.instance.stage_manager.player_characters[0])):
            # Player casting, target all bosses
            targets = [boss for boss in GameEngine.instance.stage_manager.current_stage.bosses 
                      if boss.is_alive() and boss.is_targetable()]
        else:
            # Boss casting, target all players
            targets = [char for char in GameEngine.instance.stage_manager.player_characters 
                      if char.is_alive() and char.is_targetable()]
        
        if not targets:
            return False
            
        # Apply mana cost with buff modifications
        modified_mana_cost = ghostly_scream.mana_cost
        for buff in caster.buffs:
            if hasattr(buff, 'modify_mana_cost'):
                modified_mana_cost = buff.modify_mana_cost(modified_mana_cost)
        caster.stats.current_mana -= modified_mana_cost
        
        # Calculate base damage
        base_damage = ghostly_scream.effects[0].value
        
        # Apply damage increases from caster's buffs
        for buff in caster.buffs:
            if hasattr(buff, 'apply_damage_increase'):
                base_damage = buff.apply_damage_increase(base_damage)
        
        # Deal damage and remove effects from all targets
        for target in targets:
            # Calculate final damage including target's debuffs
            damage = base_damage
            for debuff in target.debuffs:
                if hasattr(debuff, 'apply_damage_increase'):
                    damage = debuff.apply_damage_increase(damage)
            
            # Deal the damage
            target.take_damage(damage)
            
            # Remove buffs and debuffs, preserving special cases
            target.buffs = [buff for buff in target.buffs if (
                (hasattr(buff, 'is_removable') and not buff.is_removable) or  # Keep buffs explicitly marked as not removable
                (hasattr(buff, 'name') and buff.name == "Boss Regeneration")  # Preserve stage 4 boss regen
            )]
            target.debuffs = [debuff for debuff in target.debuffs if (hasattr(debuff, 'is_removable') and not debuff.is_removable)]
        
        # Call on_damage_dealt for buffs that need it (with total damage dealt)
        total_damage = base_damage * len(targets)
        for buff in caster.buffs:
            if hasattr(buff, 'on_damage_dealt'):
                buff.on_damage_dealt(total_damage)
        
        # Start cooldown
        ghostly_scream.current_cooldown = ghostly_scream.cooldown
        return True
    
    ghostly_scream.use = ghostly_scream_use
    
    # Add abilities to Kagome
    kagome.add_ability(golden_arrow)
    kagome.add_ability(golden_arrow_storm)
    kagome.add_ability(spiritwalk)
    kagome.add_ability(ghostly_scream)
    
    return kagome 