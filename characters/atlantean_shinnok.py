import pygame
import random
from typing import List
import types
from characters.base_character import Character, Stats
from abilities.base_ability import Ability, AbilityEffect, StatusEffect

class SkeletalBarrierBuff(StatusEffect):
    """Buff that has 50% chance to nullify damage and effects"""
    def __init__(self):
        super().__init__(
            type="custom",  # Use custom type to avoid default tooltip behavior
            value=50,  # 50% chance to nullify
            duration=3,  # 3 turns
            icon=pygame.image.load("assets/buffs/skeletal_barrier.png")
        )
        self.name = "Skeletal Barrier"
        self.description = "50% chance to nullify incoming damage and effects"
        self.is_removable = True
    
    def update(self):
        """Update the buff and return True if it should continue"""
        self.duration -= 1
        return self.duration > 0
    
    def should_nullify(self) -> bool:
        """Check if this instance should nullify damage"""
        return random.random() < (self.value / 100)
    
    def on_damage_taken(self, damage: int) -> int:
        """Handle incoming damage"""
        if self.should_nullify():
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    "Skeletal Barrier nullifies the damage!",
                    (80, 255, 120)  # Use green color for defense messages
                )
            return 0
        return damage
    
    def get_tooltip_title(self) -> str:
        return "Skeletal Barrier"
    
    def get_tooltip_text(self) -> str:
        effects = [
            "Effects:",
            "• 50% chance to nullify incoming damage",
            "• 50% chance to nullify incoming ability effects",
            f"• {self.duration} turns remaining"
        ]
        return "\n".join(effects)

def create_atlantean_shinnok():
    """Create and return an instance of Atlantean Shinnok"""
    
    # Create base stats for Shinnok
    stats = Stats(
        max_hp=12000,
        current_hp=12000,
        max_mana=1000,
        current_mana=1000,
        attack=100,
        defense=20,
        speed=6
    )
    
    # Create the character instance
    shinnok = Character("Atlantean Shinnok", stats, "assets/characters/atlantean_shinnok.png")
    
    # Create Magical Spheres ability with multiple hits
    class MagicalSpheresAbility(Ability):
        def __init__(self):
            super().__init__(
                name="Magical Spheres",
                description="Strikes 6 times with magical spheres, each dealing 385 damage to a random enemy.",
                icon_path="assets/abilities/magical_spheres.png",
                effects=[AbilityEffect("damage", 385)],  # Base damage per hit
                cooldown=3,
                mana_cost=80
            )
            self.hit_count = 0
            self.max_hits = 6
            self.hit_timer = 0
            self.hit_delay = 850  # 0.85 seconds in milliseconds
            self.is_executing = False
            self.current_targets = None
            self.caster = None
            self.last_update_time = 0
            
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
                self.last_update_time = self.hit_timer
                self.current_targets = targets
                self.caster = caster
                
                # Execute first hit immediately
                self.execute_hit()
            
            # Don't end turn while executing
            return False
            
        def execute_hit(self):
            """Execute a single hit of the multi-hit sequence"""
            from engine.game_engine import GameEngine
            if not GameEngine.instance:
                return
                
            # Get all valid targets
            valid_targets = [char for char in GameEngine.instance.stage_manager.player_characters 
                           if char.is_alive() and char.is_targetable()]
            
            if not valid_targets:
                return
                
            # Choose a random target for this hit
            target = random.choice(valid_targets)
            
            # Calculate final damage
            final_damage = self.effects[0].value
            
            # Apply damage increases from caster's buffs
            for buff in self.caster.buffs:
                if hasattr(buff, 'apply_damage_increase'):
                    final_damage = buff.apply_damage_increase(final_damage)
            
            # Apply damage increases from target's debuffs
            for debuff in target.debuffs:
                if hasattr(debuff, 'apply_damage_increase'):
                    final_damage = debuff.apply_damage_increase(final_damage)
            
            # Deal the damage
            target.take_damage(final_damage)
            
            # Log the hit
            if GameEngine.instance:
                hit_number = self.hit_count + 1
                GameEngine.instance.battle_log.add_message(
                    f"Magical Sphere {hit_number}/6 hits {target.name} for {final_damage} damage!",
                    GameEngine.instance.battle_log.DAMAGE_COLOR
                )
            
            self.hit_count += 1
            self.hit_timer = pygame.time.get_ticks()
            
        def update(self):
            """Update the ability state"""
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
    
    # Create Skeletal Bubble Barrier ability
    class SkeletalBubbleBarrierAbility(Ability):
        def __init__(self):
            super().__init__(
                name="Skeletal Bubble Barrier",
                description="Places a barrier that has a 50% chance to nullify incoming damage and ability effects.",
                icon_path="assets/abilities/skeletal_barrier.png",
                effects=[
                    AbilityEffect(
                        type="buff",
                        value=50,  # 50% chance to nullify
                        duration=3,  # Duration of the barrier
                        chance=1.0  # Always applies the buff
                    )
                ],
                cooldown=11,
                mana_cost=100,
                auto_self_target=True  # Always targets self
            )

        def use(self, caster: Character, targets: List[Character]) -> bool:
            if not self.can_use(caster):
                return False

            # Create and apply the buff
            barrier_buff = SkeletalBarrierBuff()
            caster.add_buff(barrier_buff)  # Use add_buff method instead of appending
            
            # Consume mana and set cooldown
            caster.stats.current_mana -= self.mana_cost
            self.current_cooldown = self.cooldown
            
            # Log the buff application
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    f"{caster.name} activates Skeletal Bubble Barrier!",
                    GameEngine.instance.battle_log.BUFF_COLOR
                )
            
            return True
    
    # Create Skeletal Handshake ability
    class SkeletalHandshakeAbility(Ability):
        def __init__(self):
            super().__init__(
                name="Skeletal Handshake",
                description="Deals 1200 damage to a random enemy.",
                icon_path="assets/abilities/skeletal_handshake.png",
                effects=[
                    AbilityEffect(
                        type="damage",
                        value=1200,
                        chance=1.0
                    )
                ],
                cooldown=4,
                mana_cost=120
            )

        def use(self, caster: Character, targets: List[Character]) -> bool:
            if not self.can_use(caster):
                return False

            # Get all valid targets
            from engine.game_engine import GameEngine
            if not GameEngine.instance:
                return False

            valid_targets = [char for char in GameEngine.instance.stage_manager.player_characters 
                           if char.is_alive() and char.is_targetable()]
            
            if not valid_targets:
                return False

            # Choose a random target
            target = random.choice(valid_targets)

            # Calculate final damage
            final_damage = self.effects[0].value
            
            # Apply damage increases from caster's buffs
            for buff in caster.buffs:
                if hasattr(buff, 'apply_damage_increase'):
                    final_damage = buff.apply_damage_increase(final_damage)
            
            # Apply damage increases from target's debuffs
            for debuff in target.debuffs:
                if hasattr(debuff, 'apply_damage_increase'):
                    final_damage = debuff.apply_damage_increase(final_damage)

            # Deal the damage
            target.take_damage(final_damage)

            # Log the damage
            GameEngine.instance.battle_log.add_message(
                f"Skeletal Handshake deals {final_damage} damage to {target.name}!",
                GameEngine.instance.battle_log.DAMAGE_COLOR
            )

            # Consume mana and set cooldown
            caster.stats.current_mana -= self.mana_cost
            self.current_cooldown = self.cooldown
            
            return True
    
    # Create and add the abilities
    magical_spheres = MagicalSpheresAbility()
    skeletal_barrier = SkeletalBubbleBarrierAbility()
    skeletal_handshake = SkeletalHandshakeAbility()
    
    shinnok.add_ability(magical_spheres)
    shinnok.add_ability(skeletal_barrier)
    shinnok.add_ability(skeletal_handshake)
    
    return shinnok 