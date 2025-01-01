import pygame
import random
from stages.base_stage import BaseStage
from characters.base_character import Character, Stats
from typing import List
from items.loot_table import LootTable
from items.crafting_materials import ShadowEssence
from items.consumables import SmokeBomb, DeepSeaEssence, MurkyWaterVial
from items.buffs import TidalCharm, VoidEssence, ShadowDagger
from abilities.base_ability import Ability, AbilityEffect
from abilities.status_effect import StatusEffect

class ShadowAssassin(Character):
    """Shadow Assassin boss class"""
    def update(self):
        """Use abilities with improved selection logic"""
        super().update()  # Call parent update for damage flash effects etc.
        
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
            
            # Increase weight for Shadowstep when low on health
            if ability.name == "Shadowstep" and self.stats.current_hp < self.stats.max_hp * 0.4:
                weight = 2.0
            # High priority for Death Mark on targets without it
            elif ability.name == "Death Mark":
                # Check if any target doesn't have Death Mark
                has_unmarked_target = any(
                    not any(buff.name == "Death Mark" for buff in target.buffs)
                    for target in valid_targets
                )
                if has_unmarked_target:
                    weight = 1.8  # High priority to mark targets
            
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

class ReptilianAssassin(Character):
    """Reptilian Assassin boss class"""
    def update(self):
        """Use abilities with improved selection logic"""
        super().update()  # Call parent update for damage flash effects etc.
        
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
            
            # Increase weight for Shadowstep when low on health
            if ability.name == "Shadowstep" and self.stats.current_hp < self.stats.max_hp * 0.4:
                weight = 2.0
            # Increase weight for Venomous Blade
            elif ability.name == "Venomous Blade":
                weight = 1.8  # High priority to use poison
            
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

class FemaleAssassin(Character):
    """Female Shadow Assassin boss class"""
    def update(self):
        """Use abilities with improved selection logic"""
        super().update()  # Call parent update for damage flash effects etc.
        
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
            
            # Increase weight for Shadowstep when low on health
            if ability.name == "Shadowstep" and self.stats.current_hp < self.stats.max_hp * 0.4:
                weight = 2.0
            # High priority for Fan of Knives when multiple targets are available
            elif ability.name == "Fan of Knives" and len(valid_targets) > 1:
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

class OctopusAssassin(Character):
    """Octopus Assassin boss class"""
    def update(self):
        """Use abilities with improved selection logic"""
        super().update()  # Call parent update for damage flash effects etc.
        
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
            
        # Prioritize abilities based on situation
        weights = []
        for ability in available_abilities:
            weight = 1.0
            
            # Increase weight for Shadowstep when low on health
            if ability.name == "Shadowstep" and self.stats.current_hp < self.stats.max_hp * 0.4:
                weight = 2.0
            # Increase weight for Drain Life when below 60% health
            elif ability.name == "Drain Life" and self.stats.current_hp < self.stats.max_hp * 0.6:
                weight = 1.5
                
            weights.append(weight)
            
        # Choose ability based on weights
        ability = random.choices(available_abilities, weights=weights, k=1)[0]
        
        if ability.auto_self_target:
            if ability.use(self, [self]):
                self.ability_used_this_turn = True
        else:
            # Find a valid target
            valid_targets = [char for char in GameEngine.instance.stage_manager.player_characters 
                           if char.is_alive() and char.is_targetable()]
            if valid_targets:
                if ability.use(self, [random.choice(valid_targets)]):
                    self.ability_used_this_turn = True

class IceWarrior(Character):
    """Ice Warrior minion class"""
    pass

# Create Venomous Blade ability for Reptilian Assassin
class PoisonDebuff(StatusEffect):
    def __init__(self, ability_icon: pygame.Surface):
        super().__init__("poison", 30, 5, ability_icon)  # Use the ability's icon
        self.name = "Venomous Blade"  # Match ability name
        self.description = "Poisoned: Taking 30 damage per turn"
        self.target = None
    
    def update(self) -> bool:
        """Update the debuff and deal poison damage"""
        if self.target and self.target.is_alive():
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                # Let take_damage handle all reductions
                damage = self.target.take_damage(30)
                GameEngine.instance.battle_log.add_message(
                    f"{self.target.name} takes {damage} poison damage!",
                    GameEngine.instance.battle_log.DAMAGE_COLOR
                )
        self.duration -= 1
        return self.duration > 0
    
    def get_tooltip_title(self) -> str:
        return "Venomous Blade"
    
    def get_tooltip_text(self) -> str:
        effects = [
            "Effects:",
            "• Taking 30 poison damage per turn",
            f"• {self.duration} turns remaining"
        ]
        return "\n".join(effects)
    
    def on_apply(self, target: Character):
        """Called when the debuff is applied"""
        self.target = target

class DeathMarkDebuff(StatusEffect):
    def __init__(self, ability_icon: pygame.Surface):
        super().__init__("death_mark", 0, 4, ability_icon)  # Use the ability's icon
        self.name = "Death Mark"
        self.description = "Marked for death, taking 45% increased damage"
        self.target = None
        self.damage_increase = 0.45  # 45% damage increase
        self.icon = ability_icon  # Store the ability icon
    
    def update(self) -> bool:
        """Update the debuff"""
        self.duration -= 1
        self.description = f"Marked for death\n{self.duration} turns remaining"
        return self.duration > 0
    
    def get_tooltip_title(self) -> str:
        return "Death Mark"
    
    def get_tooltip_text(self) -> str:
        effects = [
            "Death Mark",
            "Target has been marked for death:",
            f"• Taking {int(self.damage_increase * 100)}% increased damage from all sources",
            f"• {self.duration} turns remaining"
        ]
        return "\n".join(effects)
    
    def on_apply(self, target: Character):
        """Called when the debuff is applied"""
        self.target = target
    
    def on_remove(self, target: Character):
        """Called when the debuff is removed"""
        self.target = None
    
    def apply_damage_increase(self, damage: int) -> int:
        """Called when calculating ability damage"""
        if self.duration > 0:
            return int(damage * (1 + self.damage_increase))
        return damage

def create_venomous_blade():
    """Create the Venomous Blade ability"""
    ability = Ability(
        name="Venomous Blade",
        description="Strike for 200 damage and poison the target for 5 turns, dealing 30 damage per turn.",
        icon_path="assets/abilities/venomous_blade.png",
        effects=[AbilityEffect("damage", 200)],  # Initial damage
        cooldown=6,
        mana_cost=60,
        auto_self_target=False  # Explicitly mark as requiring a target
    )
    
    def venomous_blade_use(caster: Character, targets: List[Character]) -> bool:
        if not ability.can_use(caster) or not targets:
            return False
        
        target = targets[0]
        if not target.is_alive() or not target.is_targetable():
            return False
            
        caster.stats.current_mana -= ability.mana_cost
        damage = target.take_damage(200)
        
        # Create poison debuff with the ability's icon
        poison = PoisonDebuff(ability.icon)
        target.add_debuff(poison)
        poison.on_apply(target)
        
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"{caster.name} strikes {target.name} with a venomous blade for {damage} damage!",
                GameEngine.instance.battle_log.DAMAGE_COLOR
            )
            GameEngine.instance.battle_log.add_message(
                f"  {target.name} is poisoned!",
                GameEngine.instance.battle_log.TEXT_COLOR
            )
        
        ability.current_cooldown = ability.cooldown
        return True
    
    ability.use = venomous_blade_use
    return ability

def create_assassin(name: str, image_path: str) -> Character:
    """Create an assassin with basic stats and auto attack ability"""
    stats = Stats(
        max_hp=6890,
        current_hp=6890,
        max_mana=2500,
        current_mana=2500,
        attack=25,
        defense=10,
        speed=15
    )
    
    assassin = Character(name, stats, image_path)
    
    # Initialize ability usage tracking
    assassin.ability_used_this_turn = False
    assassin.last_turn_count = -1
    
    # Create basic auto attack ability
    auto_attack = Ability(
        name="Assassin Strike",
        description="A swift strike dealing 355 damage",
        icon_path="assets/abilities/assassin_strike.png",
        effects=[AbilityEffect("damage", 355)],
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
    
    assassin.add_ability(auto_attack)
    
    # Create Shadowstep ability with adjusted costs
    shadowstep = Ability(
        name="Shadowstep",
        description="Enter stealth for 3 turns, becoming untargetable.",
        icon_path="assets/abilities/shadowstep.png",
        effects=[],  # Custom handling in use method
        cooldown=6,  # Reduced from 9
        mana_cost=60,  # Reduced from 100
        auto_self_target=True
    )
    
    # Create custom stealth buff
    class StealthBuff(StatusEffect):
        def __init__(self):
            super().__init__("stealth", 0, 3, shadowstep.icon)
            self.name = "Stealthed"
            self.description = "Can't be targeted"
            self.original_alpha = None
            self.target = None
        
        def update(self):
            """Update the buff and return True if it should continue"""
            self.duration -= 1
            self.description = "Can't be targeted"  # Keep description simple and consistent
            
            # If buff is expiring, restore opacity
            if self.duration <= 0 and self.target:
                if self.original_alpha is not None:
                    self.target.image.set_alpha(self.original_alpha)
                from engine.game_engine import GameEngine
                if GameEngine.instance:
                    GameEngine.instance.battle_log.add_message(
                        f"{self.target.name} emerges from the shadows!",
                        GameEngine.instance.battle_log.TEXT_COLOR
                    )
            
            return self.duration > 0
        
        def get_tooltip_title(self) -> str:
            return "Stealthed"
        
        def get_tooltip_text(self) -> str:
            return self.description
        
        def is_stealthed(self) -> bool:
            """Return True if the buff is active"""
            return self.duration > 0
        
        def on_apply(self, target: Character):
            """Called when the buff is applied"""
            self.target = target  # Store reference to target
            self.original_alpha = target.image.get_alpha()  # Store original alpha
            target.image.set_alpha(51)  # 20% opacity
        
        def on_remove(self, target: Character):
            """Called when the buff is removed"""
            if self.original_alpha is not None:
                target.image.set_alpha(self.original_alpha)  # Restore original alpha
    
    # Override use method to handle stealth
    def shadowstep_use(caster: Character, targets: List[Character]) -> bool:
        if not shadowstep.can_use(caster):
            return False
        
        # Deduct mana cost
        caster.stats.current_mana -= shadowstep.mana_cost
        
        # Create and add stealth buff
        buff = StealthBuff()
        caster.add_buff(buff)
        buff.on_apply(caster)  # Apply transparency effect
        
        # Log the stealth
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"{caster.name} vanishes into the shadows!",
                GameEngine.instance.battle_log.TEXT_COLOR
            )
        
        # Start cooldown
        shadowstep.current_cooldown = shadowstep.cooldown
        return True
    
    shadowstep.use = shadowstep_use
    assassin.add_ability(shadowstep)
    
    return assassin

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

def create_drain_life():
    """Create the Drain Life ability"""
    ability = Ability(
        name="Drain Life",
        description="Drain 350 HP from the target and heal yourself for the same amount.",
        icon_path="assets/abilities/drain_life.png",
        effects=[AbilityEffect("damage", 350)],  # Initial damage
        cooldown=3,
        mana_cost=50
    )
    
    def drain_life_use(caster: Character, targets: List[Character]) -> bool:
        if not ability.can_use(caster) or not targets:
            return False
        
        target = targets[0]
        if not target.is_alive() or not target.is_targetable():
            return False
            
        caster.stats.current_mana -= ability.mana_cost
        damage = target.take_damage(350)
        
        # Heal the caster for the same amount
        heal_amount = caster.heal(damage)
        
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"{caster.name} drains {damage} life from {target.name}!",
                GameEngine.instance.battle_log.DAMAGE_COLOR
            )
            if heal_amount > 0:
                GameEngine.instance.battle_log.add_message(
                    f"  {caster.name} is healed for {heal_amount} HP!",
                    GameEngine.instance.battle_log.HEAL_COLOR
                )
        
        ability.current_cooldown = ability.cooldown
        return True
    
    ability.use = drain_life_use
    return ability

def create_fan_of_knives():
    """Create the Fan of Knives ability"""
    ability = Ability(
        name="Fan of Knives",
        description="Throw a fan of knives dealing 555 damage to all enemies.",
        icon_path="assets/abilities/fan_of_knives.png",
        effects=[AbilityEffect("damage", 555)],
        cooldown=9,
        mana_cost=85,
        auto_self_target=True  # AoE abilities are typically self-targeted
    )
    
    def fan_of_knives_use(caster: Character, targets: List[Character]) -> bool:
        if not ability.can_use(caster):
            return False
        
        # Get all valid targets
        from engine.game_engine import GameEngine
        if not GameEngine.instance:
            return False
            
        valid_targets = [char for char in GameEngine.instance.stage_manager.player_characters 
                        if char.is_alive() and char.is_targetable()]
        
        if not valid_targets:
            return False
        
        caster.stats.current_mana -= ability.mana_cost
        total_damage = 0
        
        # Deal damage to all targets
        for target in valid_targets:
            damage = target.take_damage(555)
            total_damage += damage
        
        # Log the damage
        GameEngine.instance.battle_log.add_message(
            f"{caster.name} throws a fan of knives dealing {total_damage} total damage!",
            GameEngine.instance.battle_log.DAMAGE_COLOR
        )
        
        ability.current_cooldown = ability.cooldown
        return True
    
    ability.use = fan_of_knives_use
    return ability

def create_death_mark():
    """Create the Death Mark ability"""
    ability = Ability(
        name="Death Mark",
        description="Mark the target for death, causing them to take 45% increased damage for 4 turns.",
        icon_path="assets/abilities/death_mark.png",
        effects=[],  # No direct damage
        cooldown=7,
        mana_cost=85,
        auto_self_target=False
    )
    
    def death_mark_use(caster: Character, targets: List[Character]) -> bool:
        if not ability.can_use(caster) or not targets:
            return False
        
        target = targets[0]
        if not target.is_alive() or not target.is_targetable():
            return False
            
        caster.stats.current_mana -= ability.mana_cost
        
        # Apply Death Mark debuff
        death_mark = DeathMarkDebuff(ability.icon)
        target.add_debuff(death_mark)
        death_mark.on_apply(target)
        
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.battle_log.add_message(
                f"{caster.name} marks {target.name} for death!",
                GameEngine.instance.battle_log.BUFF_COLOR  # Use BUFF_COLOR since DEBUFF_COLOR doesn't exist
            )
        
        ability.current_cooldown = ability.cooldown
        return True
    
    ability.use = death_mark_use
    return ability

class Stage3(BaseStage):
    def __init__(self):
        super().__init__(
            stage_number=3,
            name="The Assassins' Ambush",
            description="Face off against four deadly assassins seeking revenge.",
            background_path="assets/backgrounds/stage3.png"
        )
        self.turn_count = 0
        self.game_started = False  # Track if player has taken first action
        
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
        self.add_loot_table(FemaleAssassin, female_loot)
    
    def setup_bosses(self) -> List[Character]:
        """Set up the four assassin bosses"""
        # Create assassins with proper classes
        shadow = create_assassin("Shadow Assassin", "assets/characters/shadow_assassin.png")
        shadow.__class__ = ShadowAssassin
        # Add Death Mark to Shadow Assassin
        shadow.add_ability(create_death_mark())
        
        reptilian = create_assassin("Reptilian Assassin", "assets/characters/reptilian_assassin.png")
        reptilian.__class__ = ReptilianAssassin
        # Add Venomous Blade to Reptilian Assassin
        reptilian.add_ability(create_venomous_blade())
        
        female = create_assassin("Shadow Assassin Elite", "assets/characters/shadow_assassin_female.png")
        female.__class__ = FemaleAssassin
        # Add Fan of Knives to Female Assassin
        female.add_ability(create_fan_of_knives())
        
        octopus = create_assassin("Octopus Assassin", "assets/characters/octopus_assassin.png")
        octopus.__class__ = OctopusAssassin
        # Add Drain Life to Octopus Assassin
        octopus.add_ability(create_drain_life())
        
        return [shadow, reptilian, female, octopus]
    
    def update_character_positions(self):
        """Update positions of all characters"""
        # Cache screen dimensions and spacing calculations
        if not hasattr(self, '_screen_dimensions'):
            self._screen_dimensions = (1920, 1080)
            self._assassin_spacing = self._screen_dimensions[0] // (len(self.bosses) + 1)
            
            # Pre-calculate assassin positions
            self._assassin_positions = []
            for i, assassin in enumerate(self.bosses, 1):
                x = self._assassin_spacing * i - assassin.image.get_width() // 2
                self._assassin_positions.append((x, 50))
        
        # Position assassins using cached positions
        for assassin, pos in zip(self.bosses, self._assassin_positions):
            assassin.position = pos
        
        # Position player characters
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            alive_players = [p for p in GameEngine.instance.stage_manager.player_characters if p.is_alive()]
            if alive_players:
                player_spacing = self._screen_dimensions[0] // (len(alive_players) + 1)
                for i, player in enumerate(alive_players, 1):
                    x = player_spacing * i - player.image.get_width() // 2
                    player.position = (x, 600)
    
    def draw(self, screen: pygame.Surface):
        """Override draw method to position assassins and player characters in horizontal lines"""
        # Draw background (optimized with convert() in base class)
        screen.blit(self.background, (0, 0))
        
        # Update all character positions
        self.update_character_positions()
        
        # Draw assassins
        for assassin in self.bosses:
            assassin.draw(screen)
    
    def on_enter(self):
        """Called when the stage is entered"""
        # Add Summon Ice Warriors ability to Sub Zero
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            # Load modifiers from all stages
            if hasattr(GameEngine.instance, 'modifier_manager'):
                # Load modifiers from all stages
                for stage_num in range(1, 6):  # Load stages 1 through 5
                    stage_modifiers = GameEngine.instance.raid_inventory.get_modifiers("atlantean_raid", stage_num)
                    
                    # Print debug info
                    print(f"\nLoading modifiers for Stage {stage_num}:")
                    print(f"Stage {stage_num} modifiers: {stage_modifiers}")
                    
                    # Load modifiers
                    for modifier_name in stage_modifiers:
                        if modifier_name in GameEngine.instance.modifier_manager.modifier_map:
                            print(f"Creating modifier: {modifier_name}")
                            modifier = GameEngine.instance.modifier_manager.modifier_map[modifier_name]()
                            modifier.activate()
                            GameEngine.instance.modifier_manager.active_modifiers.append(modifier)
                
                print(f"Total active modifiers: {len(GameEngine.instance.modifier_manager.active_modifiers)}")
                for mod in GameEngine.instance.modifier_manager.active_modifiers:
                    print(f"  - {mod.name} (active: {mod.is_active})")
            
            subzero = GameEngine.instance.stage_manager.player_characters[0]
            
            # Create Summon Ice Warriors ability
            summon_warriors = Ability(
                name="Summon Ice Warriors",
                description="Call forth frozen warriors to aid in battle.",
                icon_path="assets/abilities/summon_ice_warriors.png",
                effects=[],  # Special handling in use method
                cooldown=10,
                mana_cost=80,
                auto_self_target=True  # Auto target self for W/ability2
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
            subzero.add_ability(summon_warriors)
            
            # Apply battle start effects for all loaded modifiers
            GameEngine.instance.modifier_manager.apply_battle_start(GameEngine.instance)
    
    def on_exit(self):
        """Called when the stage is completed"""
        # Save modifiers when stage is completed
        from engine.game_engine import GameEngine
        if GameEngine.instance and hasattr(GameEngine.instance, 'modifier_manager'):
            GameEngine.instance.modifier_manager.save_modifiers(GameEngine.instance)
    
    def on_turn_end(self):
        """Called at the end of each turn"""
        self.turn_count += 1
        
        # Apply modifier effects at turn end
        from engine.game_engine import GameEngine
        if GameEngine.instance and hasattr(GameEngine.instance, 'modifier_manager'):
            GameEngine.instance.modifier_manager.apply_turn_end(GameEngine.instance)
    
    def update(self):
        """Update stage state"""
        super().update()  # Call parent update method
        
        # Update character positions
        self.update_character_positions() 
    
    def on_player_action(self):
        """Called when player takes an action"""
        self.game_started = True 