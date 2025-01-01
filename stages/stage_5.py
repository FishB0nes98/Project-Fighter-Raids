from stages.base_stage import BaseStage
from characters.base_character import Character, Stats
from characters.atlantean_zasalamel import create_atlantean_zasalamel
from characters.subzero import create_subzero
from characters.atlantean_kotal_kahn import create_atlantean_kotal_kahn
from typing import List
import pygame
import random
from abilities.base_ability import Ability, AbilityEffect, StatusEffect
from stages.stage_3 import (
    create_death_mark, create_venomous_blade, create_fan_of_knives, create_drain_life
)


class ShadowAssassin(Character):
    """Shadow Assassin minion class"""
    def __init__(self):
        stats = Stats(
            max_hp=1500,  # Reduced from 2200
            current_hp=1500,  # Reduced from 2200
            max_mana=0,
            current_mana=0,
            attack=40,  # Reduced from 60
            defense=5,  # Reduced from 10
            speed=7
        )
        super().__init__("Shadow Assassin", stats, "assets/characters/shadow_assassin.png")
        
        # Initialize ability usage tracking
        self.ability_used_this_turn = False
        self.last_turn_count = -1
        
        # Create Shadow Strike ability
        shadow_strike = Ability(
            name="Assassin Strike",
            description="A swift strike from the shadows dealing 200 damage",  # Reduced from 300
            icon_path="assets/abilities/assassin_strike.png",
            effects=[AbilityEffect("damage", 200)],  # Reduced from 300
            cooldown=0,
            mana_cost=0,
            can_self_target=False
        )
        self.add_ability(shadow_strike)
    
    def update(self):
        """Use abilities automatically"""
        Character.update(self)  # Call Character's update method directly
        
        # Reset ability usage flag at the start of each turn
        from engine.game_engine import GameEngine
        if not GameEngine.instance:
            return
        stage = GameEngine.instance.stage_manager.current_stage
        
        # Don't use abilities until game has started
        if not stage.game_started:
            return
            
        # Don't use abilities if debug console is open
        if GameEngine.instance.debug_console.visible:
            return
            
        if stage.turn_count > self.last_turn_count:
            self.ability_used_this_turn = False
            self.last_turn_count = stage.turn_count
        
        # Don't use another ability if we've already used one this turn
        if self.ability_used_this_turn:
            return
            
        # Get all available abilities that can be used
        available_abilities = [ability for ability in self.abilities if ability.can_use(self)]
        if not available_abilities:
            return
            
        # Get valid targets first
        valid_targets = [char for char in GameEngine.instance.stage_manager.player_characters 
                        if char.is_alive() and char.is_targetable()]
        if not valid_targets:
            return
            
        # Prioritize abilities based on situation
        weights = []
        for ability in available_abilities:
            weight = 1.0
            
            # High priority for Death Mark on targets without it
            if ability.name == "Death Mark":
                # Check if any target doesn't have Death Mark
                has_unmarked_target = any(
                    not any(buff.name == "Death Mark" for buff in target.buffs)
                    for target in valid_targets
                )
                if has_unmarked_target:
                    weight = 2.0  # High priority to mark targets
            
            weights.append(weight)
            
        # Choose ability based on weights
        ability = random.choices(available_abilities, weights=weights, k=1)[0]
        
        if ability.auto_self_target:
            if ability.use(self, [self]):
                self.ability_used_this_turn = True
        else:
            if ability.name == "Death Mark":
                # Prioritize targets that don't have Death Mark
                unmarked_targets = [
                    target for target in valid_targets
                    if not any(buff.name == "Death Mark" for buff in target.buffs)
                ]
                if unmarked_targets:
                    target = random.choice(unmarked_targets)
                else:
                    target = random.choice(valid_targets)
            else:
                target = random.choice(valid_targets)
                
            if ability.use(self, [target]):
                self.ability_used_this_turn = True

class EliteShadowAssassin(Character):
    """Elite Shadow Assassin minion class"""
    def __init__(self):
        stats = Stats(
            max_hp=3500,
            current_hp=3500,
            max_mana=0,
            current_mana=0,
            attack=80,
            defense=15,
            speed=8
        )
        super().__init__("Elite Shadow Assassin", stats, "assets/characters/shadow_assassin_female.png")
        
        # Initialize ability usage tracking
        self.ability_used_this_turn = False
        self.last_turn_count = -1
        
        # Create Shadow Strike ability
        shadow_strike = Ability(
            name="Assassin Strike",
            description="A powerful strike from the shadows dealing 450 damage",
            icon_path="assets/abilities/assassin_strike.png",
            effects=[AbilityEffect("damage", 450)],
            cooldown=0,
            mana_cost=0,
            can_self_target=False
        )
        self.add_ability(shadow_strike)
    
    def update(self):
        """Use abilities automatically"""
        Character.update(self)  # Call Character's update method directly
        
        # Reset ability usage flag at the start of each turn
        from engine.game_engine import GameEngine
        if not GameEngine.instance:
            return
        stage = GameEngine.instance.stage_manager.current_stage
        
        # Don't use abilities until game has started
        if not stage.game_started:
            return
            
        # Don't use abilities if debug console is open
        if GameEngine.instance.debug_console.visible:
            return
            
        if stage.turn_count > self.last_turn_count:
            self.ability_used_this_turn = False
            self.last_turn_count = stage.turn_count
        
        # Don't use another ability if we've already used one this turn
        if self.ability_used_this_turn:
            return
            
        # Get all available abilities that can be used
        available_abilities = [ability for ability in self.abilities if ability.can_use(self)]
        if not available_abilities:
            return
            
        # Get valid targets first
        valid_targets = [char for char in GameEngine.instance.stage_manager.player_characters 
                        if char.is_alive() and char.is_targetable()]
        if not valid_targets:
            return
            
        # Prioritize abilities based on situation
        weights = []
        for ability in available_abilities:
            weight = 1.0
            
            # High priority for Fan of Knives when multiple targets are available
            if ability.name == "Fan of Knives" and len(valid_targets) > 1:
                weight = 2.0  # Higher priority with multiple targets
            elif ability.name == "Fan of Knives":
                weight = 1.5  # Still good priority with single target
            
            weights.append(weight)
            
        # Choose ability based on weights
        ability = random.choices(available_abilities, weights=weights, k=1)[0]
        
        if ability.auto_self_target:
            if ability.use(self, [self]):
                self.ability_used_this_turn = True
        else:
            # Choose a random valid target
            target = random.choice(valid_targets)
            if ability.use(self, [target]):
                self.ability_used_this_turn = True

class IceWarrior(Character):
    """Ice Warrior minion class"""
    def take_damage(self, amount: int):
        damage = super().take_damage(amount)
        
        # If the ice warrior died from this damage, remove it from player characters
        if not self.is_alive():
            from engine.game_engine import GameEngine
            if GameEngine.instance and GameEngine.instance.stage_manager:
                if self in GameEngine.instance.stage_manager.player_characters:
                    GameEngine.instance.stage_manager.player_characters.remove(self)
        
        return damage

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
        description="A freezing strike that deals 195 damage and heals Sub Zero for 50% of the damage dealt",
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
                if enemy.is_alive() and enemy.is_targetable():
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

class ShadowProtectionBuff:
    """Buff that makes Zasalamel immune to damage while any assassins are present"""
    def __init__(self):
        self.type = "custom"
        self.name = "Shadow Protection"
        self.description = "Protected by Assassins - Immune to damage"
        self.duration = 9999  # Effectively permanent
        self.heal_per_turn = 0
        self.icon = pygame.image.load("assets/abilities/shadow_protection.png")  # Use dedicated immunity icon
        self.is_removable = False
        
    def update(self):
        """Update the buff duration"""
        return True  # Never expires naturally
        
    def on_damage_taken(self, amount):
        """Make character immune to damage"""
        return 0
        
    def get_tooltip_title(self):
        return self.name
        
    def get_tooltip_text(self):
        return self.description
        
    def on_apply(self, target):
        """Called when buff is applied"""
        # Add visual effect - blue-white tint
        if not hasattr(target, 'immune_image'):
            target.immune_image = target.image.copy()
            # Create blue-white tint (60% original, 40% blue-white)
            blue_white = pygame.Surface(target.image.get_size()).convert_alpha()
            blue_white.fill((200, 220, 255))  # Light blue-white color
            target.immune_image.blit(blue_white, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            # Blend with original to keep some detail
            target.immune_image.set_alpha(102)  # 40% opacity
            temp = target.original_image.copy()
            temp.blit(target.immune_image, (0, 0))
            target.immune_image = temp
        target.image = target.immune_image
        
    def on_remove(self, target):
        """Called when buff is removed"""
        # Restore original image
        target.image = target.original_image.copy()

def update_zasalamel_immunity():
    """Update Zasalamel's immunity based on assassin presence"""
    from engine.game_engine import GameEngine
    if not GameEngine.instance or not GameEngine.instance.stage_manager.current_stage:
        return
        
    stage = GameEngine.instance.stage_manager.current_stage
    
    # Find Zasalamel
    zasalamel = next((boss for boss in stage.bosses if boss.name == "Atlantean Zasalamel"), None)
    if not zasalamel:
        return
        
    # Check if any assassins are alive
    has_assassin = any(
        isinstance(boss, (ShadowAssassin, ReptilianAssassin, FemaleAssassin, OctopusAssassin)) 
        and boss.is_alive() 
        for boss in stage.bosses
    )
    
    # Add or remove immunity buff
    has_immunity = any(isinstance(buff, ShadowProtectionBuff) for buff in zasalamel.buffs)
    
    if has_assassin and not has_immunity:
        zasalamel.add_buff(ShadowProtectionBuff())
        # Log the effect
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                "The assassins protect Zasalamel from all damage!",
                GameEngine.instance.battle_log.TEXT_COLOR
            )
    elif not has_assassin and has_immunity:
        # Remove immunity buff
        zasalamel.buffs = [buff for buff in zasalamel.buffs if not isinstance(buff, ShadowProtectionBuff)]
        # Log the effect
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                "Zasalamel's protection fades as the assassins fall!",
                GameEngine.instance.battle_log.TEXT_COLOR
            )

class Stage5(BaseStage):
    def __init__(self):
        super().__init__(
            stage_number=5,
            name="The Shadow's Domain",
            description="Face off against Atlantean Zasalamel and his shadow assassins.",
            background_path="assets/backgrounds/stage5.png"
        )
        self.turn_count = 0
        self.last_spawn_turn = 0
        self.game_started = False  # Track if player has taken first action
        
        # Set up loot tables (can be expanded later)
        from items.loot_table import LootTable
        from items.crafting_materials import ShadowEssence
        from items.consumables import (
            SmokeBomb, DeepSeaEssence, MurkyWaterVial, AbyssalEcho,
            ManaPotion, CursedWaterVial, UnderwaterCursedShell
        )
        from items.buffs import TidalCharm, VoidEssence, ShadowDagger
        from items.legendary_items import ZasalamelsScythe

        zasalamel_loot = LootTable(min_total_drops=2, max_total_drops=9)  # 2-9 items
        zasalamel_loot.add_entry(AbyssalEcho, 10.0, 0, 1)          # 10% chance for Abyssal Echo
        zasalamel_loot.add_entry(CursedWaterVial, 100.0, 1, 2)     # 100% chance for 1-2 Cursed Water Vial
        zasalamel_loot.add_entry(ManaPotion, 50.0, 0, 1)           # 50% chance for Mana Potion
        zasalamel_loot.add_entry(ShadowEssence, 70.0, 0, 1)        # 70% chance for Shadow Essence
        zasalamel_loot.add_entry(UnderwaterCursedShell, 80.0, 0, 1) # 80% chance for Underwater Cursed Shell
        zasalamel_loot.add_entry(VoidEssence, 20.0, 0, 1)          # 20% chance for Void Essence
        zasalamel_loot.add_entry(ZasalamelsScythe, 2.0, 0, 1)      # 2% chance for Zasalamel's Scythe
        self.add_loot_table(type(create_atlantean_zasalamel()), zasalamel_loot)
        
        # Set up loot tables for each assassin type
        octopus_loot = LootTable(min_total_drops=1, max_total_drops=3)
        octopus_loot.add_entry(VoidEssence, 25.0, 0, 1)      # 25% chance for Void Essence
        octopus_loot.add_entry(DeepSeaEssence, 25.0, 0, 1)   # 25% chance for Deep Sea Essence
        octopus_loot.add_entry(SmokeBomb, 55.0, 0, 1)        # 55% chance for Smoke Bomb
        octopus_loot.add_entry(ShadowEssence, 25.0, 0, 1)    # 25% chance for Shadow Essence
        octopus_loot.add_entry(ShadowDagger, 2.0, 0, 1)      # 2% chance for Shadow Dagger
        self.add_loot_table(OctopusAssassin, octopus_loot)
        
        reptilian_loot = LootTable(min_total_drops=2, max_total_drops=6)
        reptilian_loot.add_entry(DeepSeaEssence, 25.0, 0, 1)  # 25% chance for Deep Sea Essence
        reptilian_loot.add_entry(SmokeBomb, 55.0, 0, 1)       # 55% chance for Smoke Bomb
        reptilian_loot.add_entry(TidalCharm, 20.0, 0, 1)      # 20% chance for Tidal Charm
        reptilian_loot.add_entry(MurkyWaterVial, 50.0, 0, 1)  # 50% chance for Murky Water Vial
        reptilian_loot.add_entry(ShadowDagger, 2.0, 0, 1)     # 2% chance for Shadow Dagger
        self.add_loot_table(ReptilianAssassin, reptilian_loot)
        
        shadow_loot = LootTable(min_total_drops=1, max_total_drops=1)
        shadow_loot.add_entry(VoidEssence, 40.0, 0, 1)     # 40% chance for Void Essence
        shadow_loot.add_entry(SmokeBomb, 65.0, 0, 1)       # 65% chance for Smoke Bomb
        shadow_loot.add_entry(ShadowDagger, 5.0, 0, 1)     # 5% chance for Shadow Dagger
        shadow_loot.add_entry(ShadowEssence, 40.0, 0, 1)   # 40% chance for Shadow Essence
        self.add_loot_table(ShadowAssassin, shadow_loot)
        
        female_loot = LootTable(min_total_drops=2, max_total_drops=4)
        female_loot.add_entry(ShadowEssence, 50.0, 0, 1)   # 50% chance for Shadow Essence
        female_loot.add_entry(SmokeBomb, 10.0, 0, 1)       # 10% chance for Smoke Bomb
        female_loot.add_entry(VoidEssence, 50.0, 0, 1)     # 50% chance for Void Essence
        female_loot.add_entry(ShadowDagger, 6.0, 0, 1)     # 6% chance for Shadow Dagger
        self.add_loot_table(EliteShadowAssassin, female_loot)
    
    def setup_bosses(self) -> List[Character]:
        """Set up Zasalamel as the main boss"""
        return [create_atlantean_zasalamel()]

    def on_enter(self):
        """Set up player characters for this stage"""
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            # Set up player characters
            subzero = create_subzero()
            kotal = create_atlantean_kotal_kahn()
            GameEngine.instance.stage_manager.player_characters = [subzero, kotal]
            
            # Create Summon Ice Warriors ability
            summon_warriors = Ability(
                name="Summon Ice Warriors",
                description="Call forth frozen warriors to aid in battle.",
                icon_path="assets/abilities/summon_ice_warriors.png",
                effects=[],  # Special handling in use method
                cooldown=10,
                mana_cost=80,
                auto_self_target=True  # Auto target self for R ability
            )
            
            # Override use method to handle summoning
            def summon_warriors_use(caster: Character, targets: List[Character]) -> bool:
                if not summon_warriors.can_use(caster):
                    return False
                
                # Deduct mana cost
                caster.stats.current_mana -= summon_warriors.mana_cost
                
                # Create and add ice warrior minions
                if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
                    # Add 2 ice warriors to player's team
                    for _ in range(2):
                        warrior = create_ice_warrior()
                        GameEngine.instance.stage_manager.player_characters.append(warrior)
                    
                    GameEngine.instance.battle_log.add_message(
                        f"{caster.name} summons Ice Warriors!",
                        GameEngine.instance.battle_log.TEXT_COLOR
                    )
                
                # Start cooldown
                summon_warriors.current_cooldown = summon_warriors.cooldown
                return True
            
            summon_warriors.use = summon_warriors_use
            
            # Add Summon Ice Warriors ability to Sub Zero
            subzero.abilities.append(summon_warriors)
            
            # Load modifiers from previous stages
            if hasattr(GameEngine.instance, 'modifier_manager'):
                # Load modifiers from previous stages
                for stage_num in range(1, 5):
                    stage_modifiers = GameEngine.instance.raid_inventory.get_modifiers("atlantean_raid", stage_num)
                    for modifier_name in stage_modifiers:
                        if modifier_name in GameEngine.instance.modifier_manager.modifier_map:
                            modifier = GameEngine.instance.modifier_manager.modifier_map[modifier_name]()
                            modifier.activate()
                            GameEngine.instance.modifier_manager.active_modifiers.append(modifier)
    
    def on_exit(self):
        """Called when the stage is completed"""
        # Save modifiers when stage is completed
        from engine.game_engine import GameEngine
        if GameEngine.instance and hasattr(GameEngine.instance, 'modifier_manager'):
            GameEngine.instance.modifier_manager.save_modifiers(GameEngine.instance)
    
    def on_turn_end(self):
        """Called at the end of each turn"""
        self.turn_count += 1
        
        # Update Zasalamel's immunity
        update_zasalamel_immunity()
        
        # Every 6 turns, spawn assassins if less than 3 are present
        if self.turn_count >= 5 and (self.turn_count - 5) % 6 == 0:
            # Count current assassins
            assassin_count = sum(1 for boss in self.bosses if isinstance(boss, (ShadowAssassin, ReptilianAssassin, FemaleAssassin, OctopusAssassin)))
            
            if assassin_count < 3:
                from engine.game_engine import GameEngine
                
                # Choose a random assassin type
                assassin_types = [
                    (ShadowAssassin, "Shadow Assassin", "assets/characters/shadow_assassin.png", create_death_mark),
                    (ReptilianAssassin, "Reptilian Assassin", "assets/characters/reptilian_assassin.png", create_venomous_blade),
                    (FemaleAssassin, "Shadow Assassin Elite", "assets/characters/shadow_assassin_female.png", create_fan_of_knives),
                    (OctopusAssassin, "Octopus Assassin", "assets/characters/octopus_assassin.png", create_drain_life)
                ]
                
                chosen_type = random.choice(assassin_types)
                assassin_class, name, image_path, special_ability_creator = chosen_type
                
                # Create base assassin with halved stats
                stats = Stats(
                    max_hp=1500,  # Significantly reduced for Stage 5
                    current_hp=1500,
                    max_mana=0,
                    current_mana=0,
                    attack=40,
                    defense=5,
                    speed=15
                )
                
                # Create the assassin
                new_assassin = Character(name, stats, image_path)
                new_assassin.__class__ = assassin_class
                
                # Initialize ability usage tracking
                new_assassin.ability_used_this_turn = False
                new_assassin.last_turn_count = -1
                
                # Create and add basic Assassin Strike with reduced damage
                auto_attack = Ability(
                    name="Assassin Strike",
                    description="A swift strike dealing 200 damage",
                    icon_path="assets/abilities/assassin_strike.png",
                    effects=[AbilityEffect("damage", 200)],
                    cooldown=0,
                    mana_cost=0
                )
                
                # Override use method to check targetable
                def assassin_strike_use(caster: Character, targets: List[Character]) -> bool:
                    if not auto_attack.can_use(caster) or not targets:
                        return False
                    
                    target = targets[0]
                    if not target.is_alive() or not target.is_targetable():
                        return False
                        
                    # Apply mana cost
                    caster.stats.current_mana -= auto_attack.mana_cost
                    
                    # Apply damage
                    damage = auto_attack.effects[0].value
                    # Apply damage increase from caster's buffs
                    for buff in caster.buffs:
                        if hasattr(buff, 'apply_damage_increase'):
                            damage = buff.apply_damage_increase(damage)
                    target.take_damage(damage)
                    
                    # Start cooldown
                    auto_attack.current_cooldown = auto_attack.cooldown
                    return True
                
                auto_attack.use = assassin_strike_use
                new_assassin.add_ability(auto_attack)
                
                # Add their special ability with reduced damage
                special_ability = special_ability_creator()
                # Reduce the damage of the special ability by 33%
                for effect in special_ability.effects:
                    if hasattr(effect, 'value'):
                        effect.value = int(effect.value * 0.67)  # Reduce to 67% of original damage
                new_assassin.add_ability(special_ability)
                
                # Add update method to use abilities
                def update(self):
                    """Use abilities automatically"""
                    Character.update(self)  # Call Character's update method directly
                    
                    # Reset ability usage flag at the start of each turn
                    from engine.game_engine import GameEngine
                    if not GameEngine.instance:
                        return
                    stage = GameEngine.instance.stage_manager.current_stage
                    
                    # Don't use abilities until game has started
                    if not stage.game_started:
                        return
                        
                    if stage.turn_count > self.last_turn_count:
                        self.ability_used_this_turn = False
                        self.last_turn_count = stage.turn_count
                    
                    # Don't use another ability if we've already used one this turn
                    if self.ability_used_this_turn:
                        return
                        
                    # Get all available abilities that can be used
                    available_abilities = [ability for ability in self.abilities if ability.can_use(self)]
                    if not available_abilities:
                        return
                        
                    # Get valid targets first
                    valid_targets = [char for char in GameEngine.instance.stage_manager.player_characters 
                                   if char.is_alive() and char.is_targetable()]
                    if not valid_targets:
                        return
                        
                    # Prioritize abilities based on situation
                    weights = []
                    for ability in available_abilities:
                        weight = 1.0
                        
                        # High priority for special abilities
                        if ability.name in ["Fan of Knives", "Death Mark", "Venomous Blade", "Drain Life"]:
                            if len(valid_targets) > 1:
                                weight = 2.0  # Higher priority with multiple targets
                            else:
                                weight = 1.5  # Still good priority with single target
                        
                        weights.append(weight)
                        
                    # Choose ability based on weights
                    ability = random.choices(available_abilities, weights=weights, k=1)[0]
                    
                    if ability.auto_self_target:
                        if ability.use(self, [self]):
                            self.ability_used_this_turn = True
                    else:
                        # Choose a random valid target
                        target = random.choice(valid_targets)
                        if ability.use(self, [target]):
                            self.ability_used_this_turn = True
                
                # Bind the update method to the assassin instance
                import types
                new_assassin.update = types.MethodType(update, new_assassin)
                
                # Add to bosses list
                self.bosses.append(new_assassin)
                
                # Log the spawn
                if GameEngine.instance:
                    GameEngine.instance.battle_log.add_message(
                        "The shadows stir...",
                        GameEngine.instance.battle_log.TEXT_COLOR
                    )
                    GameEngine.instance.battle_log.add_message(
                        f"  A {name} emerges!",
                        GameEngine.instance.battle_log.TEXT_COLOR
                    )
                
                # Update Zasalamel's immunity after spawning
                update_zasalamel_immunity()
        
        # Apply modifier effects at turn end
        from engine.game_engine import GameEngine
        if GameEngine.instance and hasattr(GameEngine.instance, 'modifier_manager'):
            GameEngine.instance.modifier_manager.apply_turn_end(GameEngine.instance)
    
    def update_character_positions(self):
        """Update positions of all characters"""
        # Cache screen dimensions and spacing calculations
        if not hasattr(self, '_screen_dimensions'):
            self._screen_dimensions = (1920, 1080)
        
        # Position all bosses in a line
        if self.bosses:
            boss_spacing = self._screen_dimensions[0] // (len(self.bosses) + 1)
            for i, boss in enumerate(self.bosses, 1):
                x = boss_spacing * i - boss.image.get_width() // 2
                boss.position = (x, 50)
        
        # Position player characters and ice warriors
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            # Get all alive friendly characters (both players and ice warriors)
            player_chars = GameEngine.instance.stage_manager.player_characters
            all_friendly_chars = [p for p in player_chars if p.is_alive() and p.image.get_alpha() != 0]
            
            if all_friendly_chars:
                char_spacing = self._screen_dimensions[0] // (len(all_friendly_chars) + 1)
                for i, char in enumerate(all_friendly_chars, 1):
                    x = char_spacing * i - char.image.get_width() // 2
                    char.position = (x, 600)
    
    def update(self):
        """Update stage state"""
        super().update()  # Call parent update method
        
        # Update character positions every frame
        self.update_character_positions() 
    
    def draw(self, screen: pygame.Surface):
        """Draw stage"""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Update character positions
        self.update_character_positions()
        
        # Draw all bosses
        for boss in self.bosses:
            boss.draw(screen)
    
    def on_player_action(self):
        """Called when player takes an action"""
        self.game_started = True 

class ReptilianAssassin(Character):
    """Reptilian Assassin minion class"""
    def __init__(self):
        stats = Stats(
            max_hp=1500,
            current_hp=1500,
            max_mana=0,
            current_mana=0,
            attack=40,
            defense=5,
            speed=7
        )
        super().__init__("Reptilian Assassin", stats, "assets/characters/reptilian_assassin.png")
        self.ability_used_this_turn = False
        self.last_turn_count = -1
        
        shadow_strike = Ability(
            name="Assassin Strike",
            description="A swift strike dealing 200 damage",
            icon_path="assets/abilities/assassin_strike.png",
            effects=[AbilityEffect("damage", 200)],
            cooldown=0,
            mana_cost=0,
            can_self_target=False
        )
        self.add_ability(shadow_strike)

class FemaleAssassin(Character):
    """Female Assassin minion class"""
    def __init__(self):
        stats = Stats(
            max_hp=1500,
            current_hp=1500,
            max_mana=0,
            current_mana=0,
            attack=40,
            defense=5,
            speed=7
        )
        super().__init__("Shadow Assassin Elite", stats, "assets/characters/shadow_assassin_female.png")
        self.ability_used_this_turn = False
        self.last_turn_count = -1
        
        shadow_strike = Ability(
            name="Assassin Strike",
            description="A swift strike dealing 200 damage",
            icon_path="assets/abilities/assassin_strike.png",
            effects=[AbilityEffect("damage", 200)],
            cooldown=0,
            mana_cost=0,
            can_self_target=False
        )
        self.add_ability(shadow_strike)

class OctopusAssassin(Character):
    """Octopus Assassin minion class"""
    def __init__(self):
        stats = Stats(
            max_hp=1500,
            current_hp=1500,
            max_mana=0,
            current_mana=0,
            attack=40,
            defense=5,
            speed=7
        )
        super().__init__("Octopus Assassin", stats, "assets/characters/octopus_assassin.png")
        self.ability_used_this_turn = False
        self.last_turn_count = -1
        
        shadow_strike = Ability(
            name="Assassin Strike",
            description="A swift strike dealing 200 damage",
            icon_path="assets/abilities/assassin_strike.png",
            effects=[AbilityEffect("damage", 200)],
            cooldown=0,
            mana_cost=0,
            can_self_target=False
        )
        self.add_ability(shadow_strike) 