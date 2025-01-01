from characters.base_character import Character, Stats
from abilities.base_ability import Ability, AbilityEffect
from typing import List

def create_kotal_kahn():
    """Create Kotal Kahn - A powerful Osh-Tekk warrior who harnesses the power of the sun"""
    # Create character stats
    stats = Stats(
        max_hp=8000,  # High HP pool as he's a warrior
        current_hp=8000,
        max_mana=400,
        current_mana=400,
        attack=90,
        defense=20,
        speed=4
    )
    
    # Create the character
    kotal_kahn = Character("Kotal Kahn", stats, "assets/characters/kotal_kahn.png")
    
    # Sunburst - AoE heal and damage ability
    sunburst = Ability(
        name="Sunburst",
        description="Harness the power of the sun to heal all allies for 400 HP and damage all enemies for 400 damage",
        icon_path="assets/abilities/sunburst.png",
        effects=[
            AbilityEffect("heal", 400),
            AbilityEffect("damage", 400)
        ],
        cooldown=5,
        mana_cost=90
    )
    
    def sunburst_use(caster: Character, targets: List[Character]) -> bool:
        if not sunburst.can_use(caster):
            return False
            
        # Apply mana cost
        caster.stats.current_mana -= sunburst.mana_cost
        
        # Get all characters from the battle
        all_characters = caster.get_all_characters_in_battle()
        
        # Heal allies
        for char in all_characters:
            if char.team == caster.team:
                heal_amount = sunburst.effects[0].value
                char.heal(heal_amount)
        
        # Damage enemies
        for char in all_characters:
            if char.team != caster.team:
                damage = sunburst.effects[1].value
                char.take_damage(damage)
        
        # Start cooldown
        sunburst.current_cooldown = sunburst.cooldown
        return True
    
    # Attach the custom use method
    sunburst.use = sunburst_use
    
    # Add abilities to the character
    kotal_kahn.abilities.append(sunburst)
    
    return kotal_kahn 