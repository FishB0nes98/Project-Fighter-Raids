from characters.base_character import Character, Stats
from abilities.base_ability import Ability, AbilityEffect
from pathlib import Path

def create_dragon_boss():
    # Create dragon boss stats
    stats = Stats(
        max_hp=200,
        current_hp=200,
        attack=20,
        defense=15,
        speed=12
    )
    
    # Create dragon boss character
    dragon = Character("Dragon", stats, "assets/bosses/dragon.png")
    
    # Create dragon abilities
    flame_breath = Ability(
        name="Flame Breath",
        description="Breathe fire on all enemies",
        icon_path="assets/abilities/flame_breath.png",
        effects=[AbilityEffect("damage", 25)],
        cooldown=2
    )
    
    tail_swipe = Ability(
        name="Tail Swipe",
        description="Swipe tail to deal damage and reduce speed",
        icon_path="assets/abilities/tail_swipe.png",
        effects=[
            AbilityEffect("damage", 15),
            AbilityEffect("debuff", -3, duration=2)
        ],
        cooldown=3
    )
    
    dragon_scales = Ability(
        name="Dragon Scales",
        description="Harden scales to increase defense",
        icon_path="assets/abilities/dragon_scales.png",
        effects=[AbilityEffect("buff", 10, duration=3)],
        cooldown=4
    )
    
    inferno = Ability(
        name="Inferno",
        description="Unleash a devastating fire attack",
        icon_path="assets/abilities/inferno.png",
        effects=[
            AbilityEffect("damage", 50),
            AbilityEffect("debuff", -5, duration=2)
        ],
        cooldown=6
    )
    
    # Add abilities to dragon
    dragon.add_ability(flame_breath)
    dragon.add_ability(tail_swipe)
    dragon.add_ability(dragon_scales)
    dragon.add_ability(inferno)
    
    return dragon 