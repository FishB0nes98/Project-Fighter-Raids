from characters.base_character import Character, Stats
from abilities.base_ability import Ability, AbilityEffect
from pathlib import Path

def create_warrior():
    # Create warrior stats
    stats = Stats(
        max_hp=100,
        current_hp=100,
        attack=15,
        defense=10,
        speed=8
    )
    
    # Create warrior character
    warrior = Character("Warrior", stats, "assets/characters/warrior.png")
    
    # Create warrior abilities
    slash = Ability(
        name="Slash",
        description="A basic sword attack",
        icon_path="assets/abilities/slash.png",
        effects=[AbilityEffect("damage", 20)],
        cooldown=0
    )
    
    shield_bash = Ability(
        name="Shield Bash",
        description="Bash with shield, dealing damage and applying defense debuff",
        icon_path="assets/abilities/shield_bash.png",
        effects=[
            AbilityEffect("damage", 15),
            AbilityEffect("debuff", -5, duration=2)
        ],
        cooldown=2
    )
    
    rally = Ability(
        name="Rally",
        description="Boost defense of all allies",
        icon_path="assets/abilities/rally.png",
        effects=[AbilityEffect("buff", 5, duration=3)],
        cooldown=4
    )
    
    execute = Ability(
        name="Execute",
        description="Powerful attack that deals more damage to low HP targets",
        icon_path="assets/abilities/execute.png",
        effects=[AbilityEffect("damage", 40)],
        cooldown=5
    )
    
    # Add abilities to warrior
    warrior.add_ability(slash)
    warrior.add_ability(shield_bash)
    warrior.add_ability(rally)
    warrior.add_ability(execute)
    
    return warrior 