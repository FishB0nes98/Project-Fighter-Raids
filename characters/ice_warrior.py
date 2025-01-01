from characters.base_character import Character, Stats
from abilities.base_ability import Ability, AbilityEffect
from typing import List

class IceWarrior(Character):
    """Ice Warrior minion class"""
    pass

def create_ice_warrior() -> Character:
    """Create an Ice Warrior minion"""
    stats = Stats(
        max_hp=850,  # Nerfed from 1000
        current_hp=850,  # Nerfed from 1000
        max_mana=0,
        current_mana=0,
        attack=0,
        defense=0,
        speed=8
    )
    
    # Create the minion character
    warrior = IceWarrior("Frozen Atlantean", stats, "assets/characters/frozen_atlantean.png")
    
    # Create Ice Strike ability
    ice_strike = Ability(
        name="Ice Strike",
        description="A freezing strike that deals 195 damage and heals Sub Zero for 50% of the damage dealt",  # Updated damage value
        icon_path="assets/abilities/ice_strike.png",
        effects=[],  # Custom handling in use method
        cooldown=1,
        mana_cost=0,
        auto_self_target=True  # Make it auto-cast like other minions
    )
    
    # Override use method to handle healing Sub Zero
    def ice_strike_use(caster: Character, targets: List[Character]) -> bool:
        if not ice_strike.can_use(caster):
            return False
        
        # Find a valid target (first enemy that's alive and targetable)
        from engine.game_engine import GameEngine
        if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
            stage = GameEngine.instance.stage_manager.current_stage
            # Since we're on player's team, target the bosses
            for enemy in stage.bosses:
                if enemy.is_alive() and enemy.is_targetable():  # Check both alive and targetable
                    # Deal damage
                    damage = 195  # Nerfed from 250
                    enemy.take_damage(damage)
                    
                    # Find Sub Zero and heal him
                    subzero = GameEngine.instance.stage_manager.player_characters[0]
                    heal_amount = damage // 2  # 50% of damage dealt
                    subzero.heal(heal_amount)
                    
                    # Log the heal
                    GameEngine.instance.battle_log.add_message(
                        f"  Sub Zero is healed for {heal_amount} HP!",
                        GameEngine.instance.battle_log.HEAL_COLOR
                    )
                    
                    # Start cooldown
                    ice_strike.current_cooldown = ice_strike.cooldown
                    return True
        
        return False
    
    ice_strike.use = ice_strike_use
    warrior.add_ability(ice_strike)
    
    # Add auto-attack behavior
    def warrior_update():
        """Auto-use Ice Strike ability"""
        if warrior.is_alive() and ice_strike.can_use(warrior):
            ice_strike.use(warrior, [])  # Targets will be found automatically
    
    warrior.update = warrior_update
    return warrior 