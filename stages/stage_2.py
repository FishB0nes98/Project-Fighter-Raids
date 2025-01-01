from stages.base_stage import BaseStage
from characters.base_character import Character, Stats
from typing import List
from items.loot_table import LootTable
from items.consumables import IceDagger, IceShard, IceFlask
from items.legendary_items import IceBlade
from characters.subzero import create_subzero
from abilities.base_ability import Ability
import pygame

class SubZero(Character):
    """Sub Zero boss class"""
    pass

class IceWarrior(Character):
    """Ice Warrior minion class"""
    pass

class Stage2(BaseStage):
    def __init__(self):
        super().__init__(
            stage_number=2,
            name="The Frozen Depths",
            description="Face off against Atlantean Sub Zero and his frozen warriors.",
            background_path="assets/backgrounds/stage2_ice.png"
        )
        self.turn_count = 0
        self.wave_spawned = False
        
        print(f"\nSetting up Stage 2 loot tables:")
        print(f"Sub Zero class: {SubZero}")
        print(f"Ice Warrior class: {IceWarrior}")
        
        # Set up Sub Zero's loot table (1-5 ice items)
        subzero_loot = LootTable(min_total_drops=1, max_total_drops=5)
        subzero_loot.add_entry(IceDagger, 25.0)  # 25% chance for Ice Dagger
        subzero_loot.add_entry(IceShard, 70.0)   # 70% chance for Ice Shard
        subzero_loot.add_entry(IceFlask, 90.0)   # 90% chance for Ice Flask
        self.add_loot_table(SubZero, subzero_loot)
        print(f"Added Sub Zero loot table with items: IceDagger(25%), IceShard(70%), IceFlask(90%)")
        
        # Ice Warriors loot table - only Ice Blade
        minion_loot = LootTable(min_total_drops=0, max_total_drops=1)
        minion_loot.add_entry(IceBlade, 0.05)  # 0.05% chance for Ice Blade
        self.add_loot_table(IceWarrior, minion_loot)
        print(f"Added Ice Warrior loot table with items: IceBlade(0.05%)")
        print("Stage 2 loot tables setup complete\n")
    
    def create_stage2_minion(self):
        """Create a Stage 2 minion: Frozen Atlantean"""
        # Create minion stats
        stats = Stats(
            max_hp=850,
            current_hp=850,
            max_mana=0,  # No mana needed
            current_mana=0,
            attack=0,
            defense=0,
            speed=8
        )
        
        # Create the minion character as IceWarrior
        frozen = IceWarrior("Frozen Atlantean", stats, "assets/characters/frozen_atlantean.png")
        
        # Create abilities
        ice_strike = Ability(
            name="Ice Strike",
            description="A freezing strike that deals 195 damage and heals Sub Zero for 50% of the damage dealt",
            icon_path="assets/abilities/ice_strike.png",
            effects=[],  # Custom handling in use method
            cooldown=1,
            mana_cost=0
        )
        
        # Override use method to handle healing Sub Zero
        def ice_strike_use(caster: Character, targets: List[Character]) -> bool:
            if not ice_strike.can_use(caster):
                return False
            
            if not targets:
                return False
                
            # Deal damage
            damage = 195
            targets[0].take_damage(damage)
            
            # Find Sub Zero and heal him
            from engine.game_engine import GameEngine
            if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
                stage = GameEngine.instance.stage_manager.current_stage
                if stage.bosses:
                    sub_zero = stage.bosses[0]  # Sub Zero is always the first boss
                    heal_amount = damage // 2  # 50% of damage dealt
                    sub_zero.heal(heal_amount)
                    
                    # Log the heal
                    GameEngine.instance.battle_log.add_message(
                        f"  Sub Zero is healed for {heal_amount} HP!",
                        GameEngine.instance.battle_log.HEAL_COLOR
                    )
            
            # Start cooldown
            ice_strike.current_cooldown = ice_strike.cooldown
            return True
        
        ice_strike.use = ice_strike_use
        
        # Add ability to minion
        frozen.add_ability(ice_strike)
        
        return frozen
    
    def setup_bosses(self) -> List[Character]:
        """Set up Sub Zero and his initial companions"""
        # Create Sub Zero with proper class
        subzero = create_subzero()
        subzero.__class__ = SubZero  # Change the instance class to SubZero
        bosses = [subzero]
        
        # Add 4 initial companions
        for _ in range(4):
            bosses.append(self.create_stage2_minion())
        
        # Add Summon Ice Warriors ability only when Sub Zero is a boss
        summon_warriors = Ability(
            name="Summon Ice Warriors",
            description="Call forth frozen warriors to aid in battle.",
            icon_path="assets/abilities/summon_ice_warriors.png",
            effects=[],  # Special handling in use method
            cooldown=10,  # Changed to 10 turns
            mana_cost=80,
            auto_self_target=True
        )
        
        # Override summon ability's use method
        def summon_warriors_use(caster: Character, targets: List[Character]) -> bool:
            if not summon_warriors.can_use(caster):
                return False
                
            # Deduct mana cost
            caster.stats.current_mana -= summon_warriors.mana_cost
            
            # Create and add ice warrior minions
            from engine.game_engine import GameEngine
            if GameEngine.instance and GameEngine.instance.stage_manager.current_stage:
                stage = GameEngine.instance.stage_manager.current_stage
                
                # Add 2 ice warriors
                for _ in range(2):
                    minion = self.create_stage2_minion()
                    stage.bosses.append(minion)
                
                # Log the summon
                GameEngine.instance.battle_log.add_message(
                    f"{caster.name} summons Ice Warriors!",
                    GameEngine.instance.battle_log.TEXT_COLOR
                )
            
            # Start cooldown at 10 turns
            summon_warriors.current_cooldown = 10
            return True
        
        summon_warriors.use = summon_warriors_use
        
        # Set initial cooldown to 10 turns
        summon_warriors.current_cooldown = 10
        
        # Add Summon Ice Warriors ability to Sub Zero when he's a boss
        bosses[0].add_ability(summon_warriors)
        
        return bosses
    
    def draw(self, screen: pygame.Surface):
        """Override draw method to position Sub Zero in the middle with ice warriors around him"""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        if not self.bosses:
            return
            
        # Get screen dimensions (cache these values)
        if not hasattr(self, '_screen_dimensions'):
            self._screen_dimensions = (1920, 1080)
        
        # Position Sub Zero in the middle
        sub_zero = self.bosses[0]  # Sub Zero is always the first boss
        center_x = self._screen_dimensions[0] // 2
        sub_zero.position = (center_x - sub_zero.image.get_width() // 2, 50)
        
        # Position ice warriors
        if len(self.bosses) > 1:
            warriors = self.bosses[1:]
            # Calculate positions for left and right of Sub Zero
            left_warriors = warriors[:len(warriors)//2]
            right_warriors = warriors[len(warriors)//2:]
            
            # Position warriors to the left of Sub Zero
            for i, warrior in enumerate(left_warriors):
                x = center_x - sub_zero.image.get_width()//2 - (i + 1) * (warrior.image.get_width() + 25) 
                warrior.position = (x, 50)  # Same height as Sub Zero
            
            # Position warriors to the right of Sub Zero
            for i, warrior in enumerate(right_warriors):
                x = center_x - sub_zero.image.get_width()//2 + ((i + 1) * (warrior.image.get_width() + 25))
                warrior.position = (x, 50)  # Same height as Sub Zero
        
        # Position player characters
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            alive_players = [p for p in GameEngine.instance.stage_manager.player_characters if p.is_alive()]
            if alive_players:
                player_spacing = self._screen_dimensions[0] // (len(alive_players) + 1)
                for i, player in enumerate(alive_players, 1):
                    x = player_spacing * i - player.image.get_width() // 2
                    player.position = (x, 600)
        
        # Draw all characters
        for boss in self.bosses:
            boss.draw(screen)
    
    def on_enter(self):
        """Called when the stage is entered"""
        # Load modifiers from previous stages
        from engine.game_engine import GameEngine
        if GameEngine.instance and hasattr(GameEngine.instance, 'modifier_manager'):
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
        
        # Add stage-specific turn mechanics here
        # For example, spawning additional enemies at certain turns
        if self.turn_count == 25 and not self.wave_spawned:
            self.wave_spawned = True
            
            # Create and add additional frozen warriors
            for _ in range(2):  # Spawn 2 more frozen warriors
                minion = self.create_stage2_minion()
                self.bosses.append(minion)
            
            # Log the event
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    "The waters grow colder...",
                    GameEngine.instance.battle_log.TEXT_COLOR
                )
                GameEngine.instance.battle_log.add_message(
                    "  More frozen warriors emerge!",
                    GameEngine.instance.battle_log.TEXT_COLOR
                )
        
        # Apply modifier effects at turn end
        from engine.game_engine import GameEngine
        if GameEngine.instance and hasattr(GameEngine.instance, 'modifier_manager'):
            GameEngine.instance.modifier_manager.apply_turn_end(GameEngine.instance) 