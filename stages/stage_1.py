from stages.base_stage import BaseStage
from characters.shadowfin_boss import create_shadowfin_boss, Piranha
from typing import List
from characters.base_character import Character
from items.loot_table import LootTable
from items.consumables import MurkyWaterVial, DeepSeaEssence, PiranhaTooth
from items.buffs import PiranhaScales, TidalCharm, VoidEssence
import pygame

class Stage1(BaseStage):
    def __init__(self):
        super().__init__(
            stage_number=1,
            name="The Dark Waters",
            description="Face off against Shadowfin, the terror of the deep.",
            background_path="assets/backgrounds/stage1.jpeg"
        )
        self.turn_count = 0
        self.piranha_wave_spawned = False
        
        # Set up loot tables
        piranha_loot = LootTable(min_total_drops=0, max_total_drops=3)  # 0-3 items total
        piranha_loot.add_entry(PiranhaTooth, 10.0, 0, 1)    # 10% chance for Piranha Tooth
        piranha_loot.add_entry(PiranhaScales, 30.0, 0, 1)   # 30% chance for Piranha Scales
        piranha_loot.add_entry(MurkyWaterVial, 60.0, 0, 1)  # 60% chance for Murky Water Vial
        self.add_loot_table(Piranha, piranha_loot)

        # Set up Shadowfin's loot table
        shadowfin_loot = LootTable(min_total_drops=2, max_total_drops=8)  # 2-8 items total
        shadowfin_loot.add_entry(MurkyWaterVial, 70.0, 0, 2)  # 70% chance for Murky Water Vial
        shadowfin_loot.add_entry(TidalCharm, 50.0, 0, 2)      # 50% chance for Tidal Charm
        shadowfin_loot.add_entry(VoidEssence, 25.0, 0, 1)     # 25% chance for Void Essence
        shadowfin_loot.add_entry(DeepSeaEssence, 40.0, 0, 2)  # 40% chance for Deep Sea Essence
        self.add_loot_table(type(create_shadowfin_boss()), shadowfin_loot)
    
    def setup_bosses(self) -> List[Character]:
        return [create_shadowfin_boss()]
    
    def on_enter(self):
        """Called when the stage is entered"""
        # Load modifiers from previous stages
        from engine.game_engine import GameEngine
        if GameEngine.instance and hasattr(GameEngine.instance, 'modifier_manager'):
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
        
        # At turn 30, spawn 3 piranhas if not already spawned
        if self.turn_count == 30 and not self.piranha_wave_spawned:
            self.piranha_wave_spawned = True
            
            # Create and add 3 piranhas
            for _ in range(3):
                piranha = Piranha()
                self.bosses.append(piranha)
            
            # Log the event
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    "The water churns violently...",
                    GameEngine.instance.battle_log.TEXT_COLOR
                )
                GameEngine.instance.battle_log.add_message(
                    "  A school of piranhas appears!",
                    GameEngine.instance.battle_log.TEXT_COLOR
                )
        
        # Apply modifier effects at turn end
        from engine.game_engine import GameEngine
        if GameEngine.instance and hasattr(GameEngine.instance, 'modifier_manager'):
            GameEngine.instance.modifier_manager.apply_turn_end(GameEngine.instance)
    
    def update_character_positions(self):
        """Update positions of all characters"""
        # Cache screen dimensions and spacing calculations
        if not hasattr(self, '_screen_dimensions'):
            self._screen_dimensions = (1920, 1080)
            
        # Position Shadowfin in the center
        if self.bosses:
            shadowfin = self.bosses[0]  # Shadowfin is always the first boss
            center_x = self._screen_dimensions[0] // 2
            shadowfin.position = (center_x - shadowfin.image.get_width() // 2, 50)
            
            # Position piranhas if they exist
            if len(self.bosses) > 1:
                piranhas = self.bosses[1:]
                # Calculate positions for left and right of Shadowfin
                left_piranhas = piranhas[:len(piranhas)//2]
                right_piranhas = piranhas[len(piranhas)//2:]
                
                # Position piranhas to the left of Shadowfin
                for i, piranha in enumerate(left_piranhas):
                    x = center_x - shadowfin.image.get_width()//2 - (i + 1) * (piranha.image.get_width() + 25)
                    piranha.position = (x, 50)  # Same height as Shadowfin
                
                # Position piranhas to the right of Shadowfin
                for i, piranha in enumerate(right_piranhas):
                    x = center_x - shadowfin.image.get_width()//2 + ((i + 1) * (piranha.image.get_width() + 25))
                    piranha.position = (x, 50)  # Same height as Shadowfin
        
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
        """Override draw method to position characters properly"""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Update all character positions
        self.update_character_positions()
        
        # Draw all bosses
        for boss in self.bosses:
            boss.draw(screen) 