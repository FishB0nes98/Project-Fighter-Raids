import pygame
from stages.base_stage import BaseStage
from characters.base_character import Character, Stats
from typing import List
from items.loot_table import LootTable
from items.consumables import DeepSeaEssence, MurkyWaterVial, LeviathanMistVial, AbyssalEcho, ManaPotion, AtlanteanTrident
from items.buffs import TidalCharm, VoidEssence
from items.crafting_materials import LeviathanScale
from abilities.base_ability import Ability, AbilityEffect
from abilities.status_effect import StatusEffect
from characters.atlantean_christie import create_atlantean_christie
from pathlib import Path
import types
from functools import partial
import math

def create_dark_leviathan():
    """Create Dark Leviathan - A powerful underwater creature boss"""
    stats = Stats(
        max_hp=21580,
        current_hp=21580,
        max_mana=9000,
        current_mana=9000,
        attack=100,
        defense=30,
        speed=4
    )
    
    # Create the boss
    leviathan = Character("Dark Leviathan", stats, "assets/characters/dark_leviathan.png")
    
    # Setup loot table
    loot_table = LootTable(min_total_drops=1, max_total_drops=3)
    loot_table.add_entry(DeepSeaEssence, 50.0, 1, 2)  # 50% chance for 1-2 Deep Sea Essence
    loot_table.add_entry(MurkyWaterVial, 40.0, 1, 1)  # 40% chance for 1 Murky Water Vial
    loot_table.add_entry(LeviathanMistVial, 30.0, 1, 1)  # 30% chance for 1 Leviathan's Mist Vial
    loot_table.add_entry(LeviathanScale, 35.0, 1, 1)  # 35% chance for 1 Leviathan Scale
    loot_table.add_entry(AbyssalEcho, 67.0, 1, 1)  # 67% chance for 1 Abyssal Echo
    loot_table.add_entry(ManaPotion, 100.0, 1, 2)  # 100% chance for 1-2 Mana Potions
    loot_table.add_entry(AtlanteanTrident, 50.0, 1, 1)  # 50% chance for 1 Atlantean Trident
    leviathan.loot_table = loot_table
    
    # Create Slam ability
    slam = Ability(
        name="Abyssal Slam",
        description="A devastating slam that creates shockwaves in the water. Has a 75% chance to increase all enemy ability cooldowns by 1 turn.",
        icon_path="assets/abilities/abyssal_slam.png",
        effects=[
            AbilityEffect("damage", 1050),
            AbilityEffect("increase_cooldowns", 1, chance=0.75)
        ],
        cooldown=2,
        mana_cost=100
    )

    # Create Wave Crush ability
    class WaveCrushDebuff(StatusEffect):
        def __init__(self, value: float, duration: int, icon: pygame.Surface):
            super().__init__("damage_taken_increase", value, duration, icon)
            self.name = "Wave Crush"
            self.description = f"Taking {int(value * 100)}% increased damage"
            self.stacks = 1  # Track number of stacks
        
        def update(self) -> bool:
            """Update the debuff"""
            self.duration -= 1
            self.description = f"Taking {int(self.value * 100)}% increased damage ({self.stacks} stacks)\n{self.duration} turns remaining"
            return self.duration > 0
        
        def get_tooltip_title(self) -> str:
            return f"Wave Crush ({self.stacks} stacks)"
        
        def get_tooltip_text(self) -> str:
            return f"Taking {int(self.value * 100)}% increased damage from all sources\n{self.duration} turns remaining"
        
        def on_damage_taken(self, damage: int) -> int:
            """Increase damage taken by the debuff percentage"""
            return int(damage * (1 + self.value))
        
        def stack(self, new_debuff):
            """Stack with another Wave Crush debuff"""
            self.value += new_debuff.value  # Add the values together
            self.duration = max(self.duration, new_debuff.duration)  # Take the longer duration
            self.stacks += 1  # Increment stack count
            self.description = f"Taking {int(self.value * 100)}% increased damage ({self.stacks} stacks)\n{self.duration} turns remaining"

    wave_crush = Ability(
        name="Wave Crush",
        description="A massive wave that deals 900 damage to all enemies and increases their damage taken by 10% for 10 turns. This effect can stack!",
        icon_path="assets/abilities/wave_crush.png",
        effects=[
            AbilityEffect("damage_all", 900),
        ],
        cooldown=6,
        mana_cost=50
    )

    # Create Monstrous Scream ability
    class DisabledAbilityDebuff(StatusEffect):
        def __init__(self, ability: Ability, duration: int, icon: pygame.Surface):
            super().__init__("custom", duration, duration, icon)
            self.name = "Disabled Ability"
            self.description = f"{ability.name} is disabled"
            self.disabled_ability = ability
            
            # Store original ability use functions and draw methods
            self.original_abilities = []
            original_draw = ability.draw if hasattr(ability, 'draw') else None
            original_use = ability.use
            original_icon = ability.icon.copy()  # Store original icon
            self.original_abilities.append((ability, original_use, original_draw, original_icon))
            
            # Override use function to disable ability
            ability.use = lambda *args, **kwargs: False
            
            # Create draw method with X overlay
            def draw_with_x(self_ability, screen):
                # Create a new surface for the X overlay
                x_size = self_ability.icon.get_width()
                x_surface = pygame.Surface((x_size, x_size), pygame.SRCALPHA)
                x_color = (255, 0, 0, 180)  # Semi-transparent red
                x_thickness = 3  # Define thickness for the X
                
                # Draw the X with a black outline for better visibility
                # Draw black outline
                outline_color = (0, 0, 0, 180)
                outline_thickness = x_thickness + 2
                pygame.draw.line(x_surface, outline_color, (0, 0), (x_size, x_size), outline_thickness)
                pygame.draw.line(x_surface, outline_color, (0, x_size), (x_size, 0), outline_thickness)
                
                # Draw red X
                pygame.draw.line(x_surface, x_color, (0, 0), (x_size, x_size), x_thickness)
                pygame.draw.line(x_surface, x_color, (0, x_size), (x_size, 0), x_thickness)
                
                # Create a new icon with the X overlay
                new_icon = self_ability.icon.copy()
                new_icon.blit(x_surface, (0, 0))
                self_ability.icon = new_icon
            
            # Apply the X overlay to the icon immediately
            draw_with_x(ability, None)
            
            # Create a new method that includes both the original functionality and our X overlay
            def combined_draw(self_ability, screen):
                # First call the original Ability.draw to handle normal ability drawing
                Ability.draw(self_ability, screen)
                # Then add our X overlay
                draw_with_x(self_ability, screen)
            
            # Bind the combined draw method to the ability
            ability.draw = types.MethodType(combined_draw, ability)
        
        def update(self) -> bool:
            """Update the debuff"""
            self.duration -= 1
            self.description = f"{self.disabled_ability.name} is disabled\n{self.duration} turns remaining"
            
            if self.duration <= 0:
                # Restore original ability functionality
                for ability, original_use, original_draw, original_icon in self.original_abilities:
                    ability.use = original_use
                    if original_draw:
                        ability.draw = original_draw
                    ability.icon = original_icon  # Restore original icon
                return False
            return True
        
        def get_tooltip_title(self) -> str:
            return f"Disabled: {self.disabled_ability.name}"
        
        def get_tooltip_text(self) -> str:
            return f"This ability has been disabled by Monstrous Scream\n{self.duration} turns remaining"

    monstrous_scream = Ability(
        name="Monstrous Scream",
        description="A terrifying scream that deals 665 damage and disables a random ability for all enemies for 8 turns.",
        icon_path="assets/abilities/monstrous_scream.png",
        effects=[
            AbilityEffect("damage_all", 665),
        ],
        cooldown=16,
        mana_cost=85
    )

    # Create Abyssal Regeneration passive ability
    class AbyssalRegenerationBuff(StatusEffect):
        def __init__(self, icon: pygame.Surface):
            super().__init__("custom", 88, -1, icon)  # -1 duration means permanent
            self.name = "Abyssal Regeneration"
            self.description = "Regenerates 88 HP at the end of each turn"
            self.heal_per_turn = 88  # This will trigger automatic healing in end_turn()
            self.is_removable = False  # Make buff immune to removal
        
        def update(self) -> bool:
            """Keep the buff active permanently"""
            return True  # Always keep the buff active
        
        def get_tooltip_title(self) -> str:
            return "Abyssal Regeneration"
        
        def get_tooltip_text(self) -> str:
            return "Passive: Regenerates 88 HP at the end of each turn\nCannot be removed"
        
        def on_remove(self, target: Character):
            """If somehow removed, reapply immediately"""
            if target and target.is_alive():
                target.add_buff(AbyssalRegenerationBuff(self.icon))
                # Log the reapplication
                from engine.game_engine import GameEngine
                if GameEngine.instance:
                    GameEngine.instance.battle_log.add_message(
                        f"{target.name}'s Abyssal Regeneration reactivates!",
                        GameEngine.instance.battle_log.BUFF_COLOR
                    )

    abyssal_regen = Ability(
        name="Abyssal Regeneration",
        description="Passive: At the end of each turn, regenerate 88 HP.",
        icon_path="assets/abilities/abyssal_regen.png",
        effects=[],  # No active effects since this is passive
        cooldown=0,  # No cooldown for passive
        mana_cost=0  # No mana cost for passive
    )

    # Mark ability as passive and add passive overlay to icon
    def mark_as_passive(ability):
        ability.is_passive = True  # Add passive flag
        
        # Create passive overlay
        icon_size = ability.icon.get_width()
        overlay = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        
        # Add a semi-transparent dark overlay
        overlay.fill((0, 0, 0, 80))
        
        # Add "PASSIVE" text
        font = pygame.font.Font(None, 20)
        text = font.render("PASSIVE", True, (255, 255, 255))
        text_rect = text.get_rect(center=(icon_size//2, icon_size//2))
        
        # Add white glow/outline to text
        glow_surface = pygame.Surface((text.get_width() + 4, text.get_height() + 4), pygame.SRCALPHA)
        glow_surface.fill((255, 255, 255, 50))
        overlay.blit(glow_surface, (text_rect.x - 2, text_rect.y - 2))
        
        # Draw the text
        overlay.blit(text, text_rect)
        
        # Apply overlay to icon
        new_icon = ability.icon.copy()
        new_icon.blit(overlay, (0, 0))
        ability.icon = new_icon
        
        # Override use method to always return False (can't be used actively)
        ability.use = lambda *args, **kwargs: False
        
        return ability

    abyssal_regen = mark_as_passive(abyssal_regen)
    
    # Override wave crush use method to apply stacking debuff
    def wave_crush_use(caster: Character, targets: List[Character]) -> bool:
        if not wave_crush.can_use(caster):
            return False

        # Deduct mana cost
        caster.stats.current_mana -= wave_crush.mana_cost

        # Deal damage to all targets
        for target in targets:
            # Apply damage reduction
            damage = 900
            damage_reduction = target.get_damage_reduction()
            reduced_damage = damage * (1 - damage_reduction / 100)
            final_damage = max(1, int(reduced_damage - target.stats.defense))
            target.take_damage(final_damage)

            # Create new debuff
            new_debuff = WaveCrushDebuff(0.1, 10, wave_crush.icon)  # 10% damage increase

            # Check for existing Wave Crush debuff
            existing_debuff = None
            for debuff in target.debuffs:
                if isinstance(debuff, WaveCrushDebuff):
                    existing_debuff = debuff
                    break

            if existing_debuff:
                # Stack with existing debuff
                existing_debuff.stack(new_debuff)
                # Log the stack
                from engine.game_engine import GameEngine
                if GameEngine.instance:
                    GameEngine.instance.battle_log.add_message(
                        f"  {target.name} takes {final_damage} damage and Wave Crush stacks! Now taking {int(existing_debuff.value * 100)}% increased damage",
                        GameEngine.instance.battle_log.DAMAGE_COLOR
                    )
            else:
                # Apply new debuff
                target.add_debuff(new_debuff)
                # Log the new debuff
                from engine.game_engine import GameEngine
                if GameEngine.instance:
                    GameEngine.instance.battle_log.add_message(
                        f"  {target.name} takes {final_damage} damage and gains Wave Crush: +10% damage taken",
                        GameEngine.instance.battle_log.DAMAGE_COLOR
                    )

        # Start cooldown
        wave_crush.current_cooldown = wave_crush.cooldown
        return True

    wave_crush.use = wave_crush_use
    
    def monstrous_scream_use(caster: Character, targets: List[Character]) -> bool:
        if not monstrous_scream.can_use(caster):
            return False
        
        # Deduct mana cost
        caster.stats.current_mana -= monstrous_scream.mana_cost
        
        # Get all enemies from the game engine
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            current_stage = GameEngine.instance.stage_manager.current_stage
            if current_stage:
                # Get player characters as targets
                enemies = GameEngine.instance.stage_manager.player_characters
                
                # Deal damage to all enemies first
                for enemy in enemies:
                    # Apply damage reduction
                    damage = 665
                    damage_reduction = enemy.get_damage_reduction()
                    reduced_damage = damage * (1 - damage_reduction / 100)
                    final_damage = max(1, int(reduced_damage - enemy.stats.defense))
                    enemy.take_damage(final_damage)
                    
                    # Log the damage
                    GameEngine.instance.battle_log.add_message(
                        f"  {enemy.name} takes {final_damage} damage from Monstrous Scream!",
                        GameEngine.instance.battle_log.DAMAGE_COLOR
                    )
                
                # Then apply ability disable effect
                for enemy in enemies:
                    # Select a random ability that isn't already disabled
                    available_abilities = [
                        ability for ability in enemy.abilities 
                        if not any(isinstance(debuff, DisabledAbilityDebuff) and debuff.disabled_ability == ability 
                                 for debuff in enemy.debuffs)
                    ]
                    
                    if available_abilities:
                        # Choose random ability to disable
                        import random
                        ability_to_disable = random.choice(available_abilities)
                        
                        # Create and apply the debuff
                        debuff = DisabledAbilityDebuff(ability_to_disable, 8, monstrous_scream.icon)
                        enemy.add_debuff(debuff)
                        
                        # Log the effect
                        GameEngine.instance.battle_log.add_message(
                            f"  {enemy.name}'s {ability_to_disable.name} is disabled for 8 turns!",
                            GameEngine.instance.battle_log.TEXT_COLOR
                        )
        
        # Start cooldown
        monstrous_scream.current_cooldown = monstrous_scream.cooldown
        return True

    monstrous_scream.use = monstrous_scream_use
    
    # Override slam use method to handle cooldown increase
    def slam_use(caster: Character, targets: List[Character]) -> bool:
        if not slam.can_use(caster):
            return False
        
        # Deduct mana cost
        caster.stats.current_mana -= slam.mana_cost
        
        # Get target
        if not targets:
            return False
        target = targets[0]
        
        # Apply damage
        damage = 1050
        damage_reduction = target.get_damage_reduction()
        reduced_damage = damage * (1 - damage_reduction / 100)
        final_damage = max(1, int(reduced_damage - target.stats.defense))
        target.take_damage(final_damage)
        
        # 75% chance to increase cooldowns
        import random
        if random.random() < 0.75:
            # Increase cooldowns of all abilities
            for ability in target.abilities:
                if not hasattr(ability, 'is_passive') or not ability.is_passive:
                    ability.current_cooldown += 1
            
            # Log the cooldown increase
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                GameEngine.instance.battle_log.add_message(
                    f"  {target.name}'s ability cooldowns are increased by 1 turn!",
                    GameEngine.instance.battle_log.TEXT_COLOR
                )
        
        # Start cooldown
        slam.current_cooldown = slam.cooldown
        return True

    slam.use = slam_use
    
    # Add abilities to Leviathan
    leviathan.add_ability(slam)
    leviathan.add_ability(wave_crush)
    leviathan.add_ability(abyssal_regen)
    leviathan.add_ability(monstrous_scream)
    
    # Apply the passive regeneration buff
    leviathan.add_buff(AbyssalRegenerationBuff(abyssal_regen.icon))
    
    return leviathan

class Stage4(BaseStage):
    def __init__(self):
        super().__init__(
            stage_number=4,
            name="The Abyssal Depths",
            description="Face off against the Dark Leviathan, an ancient creature of the deep.",
            background_path="assets/backgrounds/stage4.png"
        )
        
        # Initialize wave tracking
        self.turn_count = 0
        self.kagome_spawned = False  # Track if Kagome has been spawned
        
        # Wave effect caching
        self._wave_surfaces_cache = {}  # Cache for wave effect surfaces
        self._wave_lines_cache = []  # Cache for wave lines
        self._screen_dimensions = None  # Cache for screen dimensions
        self._wave_pattern_cache = None  # Cache for wave pattern
        self.wave_animation_frame = 0
        self.wave_alpha = 0
        self.is_wave_active = False
        self.wave_start_time = 0
        self.wave_duration = 3
        
        # Set up loot tables
        leviathan = create_dark_leviathan()
        self.add_loot_table(type(leviathan), leviathan.loot_table)
    
    def setup_bosses(self) -> List[Character]:
        """Set up the Dark Leviathan boss"""
        return [create_dark_leviathan()]
    
    def _create_wave_pattern(self, screen_width: int, screen_height: int):
        """Create and cache wave pattern"""
        if self._wave_pattern_cache is None:
            wave_height = 20
            wave_length = 200
            points_list = []
            
            # Generate fewer waves for better performance
            for y in range(0, screen_height, wave_height * 4):
                for x in range(-wave_length, screen_width + wave_length, wave_length):
                    points = []
                    # Use fewer points per wave
                    for i in range(0, wave_length + 1, 10):
                        points.append((x + i, y))  # Store only x,y base positions
                    points_list.append(points)
            
            self._wave_pattern_cache = points_list
    
    def _get_wave_surface(self, screen_size: tuple) -> pygame.Surface:
        """Get or create wave effect surface"""
        cache_key = (screen_size, self.wave_animation_frame, self.wave_alpha)
        
        if cache_key not in self._wave_surfaces_cache:
            # Create new surface
            surface = pygame.Surface(screen_size, pygame.SRCALPHA)
            
            # Create wave pattern if not cached
            if not self._wave_pattern_cache:
                self._create_wave_pattern(screen_size[0], screen_size[1])
            
            # Draw waves using cached pattern
            wave_color = (64, 156, 255, self.wave_alpha)
            wave_height = 20
            
            for base_points in self._wave_pattern_cache:
                points = []
                for x, y in base_points:
                    # Apply wave animation
                    angle = (x / 200) * math.pi * 2  # 200 is wave_length
                    new_y = y + math.sin(angle + self.wave_animation_frame / 10) * wave_height
                    points.append((x, new_y))
                
                if len(points) > 1:
                    pygame.draw.lines(surface, wave_color, False, points, 3)
            
            # Cache the surface
            self._wave_surfaces_cache[cache_key] = surface
            
            # Clear old cache entries if too many
            if len(self._wave_surfaces_cache) > 10:
                old_keys = list(self._wave_surfaces_cache.keys())[:-10]
                for key in old_keys:
                    del self._wave_surfaces_cache[key]
        
        return self._wave_surfaces_cache[cache_key]
    
    def update_character_positions(self):
        """Update positions of all characters"""
        # Cache screen dimensions and spacing calculations
        if not self._screen_dimensions:
            self._screen_dimensions = (1920, 1080)
            
        # Position Dark Leviathan in the center
        if self.bosses:
            leviathan = self.bosses[0]  # Dark Leviathan is always the first boss
            center_x = self._screen_dimensions[0] // 2
            leviathan.position = (center_x - leviathan.image.get_width() // 2, 50)
        
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
        """Override draw method to add wave effect"""
        # Draw background
        screen.blit(self.background, (0, 0))
        
        # Update character positions
        self.update_character_positions()
        
        # Draw wave effect if active
        if self.is_wave_active:
            current_time = pygame.time.get_ticks() / 1000.0
            if current_time - self.wave_start_time > self.wave_duration:
                self.is_wave_active = False
                self.wave_alpha = 0
                self._wave_surfaces_cache.clear()  # Clear cache when effect ends
            else:
                # Update wave animation
                self.wave_animation_frame = (self.wave_animation_frame + 1) % 360
                if self.wave_alpha < 128:
                    self.wave_alpha = min(128, self.wave_alpha + 8)
                
                # Get cached wave surface
                wave_surface = self._get_wave_surface(screen.get_size())
                screen.blit(wave_surface, (0, 0))
        else:
            self.wave_alpha = max(0, self.wave_alpha - 8)
            if self.wave_alpha == 0:
                self._wave_surfaces_cache.clear()  # Clear cache when effect fully fades
        
        # Draw all characters
        for boss in self.bosses:
            boss.draw(screen)
        
        # Draw player characters
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            alive_players = [p for p in GameEngine.instance.stage_manager.player_characters if p.is_alive()]
            if alive_players:
                player_spacing = screen.get_width() // (len(alive_players) + 1)
                for i, player in enumerate(alive_players, 1):
                    x = player_spacing * i - player.image.get_width() // 2
                    player.position = (x, 600)
                    player.draw(screen)
    
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
    
    def update(self):
        """Update stage state"""
        super().update()
        self.update_character_positions()
    
    def on_turn_end(self):
        """Called at the end of each turn"""
        self.turn_count += 1
        
        # At turn 10, spawn Atlantean Kagome if not already spawned
        if self.turn_count == 10 and not self.kagome_spawned:
            self.kagome_spawned = True
            
            # Create and add Atlantean Kagome to player characters
            from characters.atlantean_kagome import create_atlantean_kagome
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                kagome = create_atlantean_kagome()
                GameEngine.instance.stage_manager.player_characters.append(kagome)
                
                # Log the event
                GameEngine.instance.battle_log.add_message(
                    "A powerful ally emerges from the depths...",
                    GameEngine.instance.battle_log.TEXT_COLOR
                )
                GameEngine.instance.battle_log.add_message(
                    "  Atlantean Kagome joins your team!",
                    GameEngine.instance.battle_log.TEXT_COLOR
                )
        
        # Every 8th turn, trigger the healing wave
        if self.turn_count % 8 == 0:
            from engine.game_engine import GameEngine
            if GameEngine.instance:
                # Get all characters (both boss and players)
                all_characters = self.bosses + GameEngine.instance.stage_manager.player_characters
                
                # Heal all characters and track total healing
                for character in all_characters:
                    if character.is_alive():
                        # Use character's heal method which handles healing buffs
                        actual_healing = character.heal(1500)
                        
                        # Log individual healing if it was modified by buffs
                        if actual_healing != 1500:
                            GameEngine.instance.battle_log.add_message(
                                f"  {character.name} recovers {actual_healing} HP from the wave!",
                                GameEngine.instance.battle_log.HEAL_COLOR
                            )
                
                # Activate wave effect
                self.is_wave_active = True
                self.wave_animation_frame = 0
                self.wave_alpha = 0
                self.wave_start_time = pygame.time.get_ticks() / 1000.0  # Current time in seconds
                self.wave_lines = []  # Clear cached lines
                
                # Log the wave effect
                GameEngine.instance.battle_log.add_message(
                    "A massive healing wave surges through the depths!",
                    GameEngine.instance.battle_log.HEAL_COLOR
                )
                # Only show base healing amount in main message
                GameEngine.instance.battle_log.add_message(
                    "  The wave restores 1500 HP to all characters!",
                    GameEngine.instance.battle_log.HEAL_COLOR
                )
        
        # Apply modifier effects at turn end
        from engine.game_engine import GameEngine
        if GameEngine.instance and hasattr(GameEngine.instance, 'modifier_manager'):
            GameEngine.instance.modifier_manager.apply_turn_end(GameEngine.instance)
    
    def handle_debug_command(self, command: str) -> bool:
        """Handle debug commands for the stage"""
        if command.startswith("turn test "):
            try:
                turn_number = int(command.split(" ")[2])
                # Set both turn counters to the target number
                self.turn_count = turn_number
                from engine.game_engine import GameEngine
                if GameEngine.instance:
                    # Set the game engine's turn counter
                    GameEngine.instance.game_state.turn_count = turn_number
                    GameEngine.instance.battle_log.add_message(
                        f"Debug: Set turn counter to {turn_number}",
                        GameEngine.instance.battle_log.BUFF_COLOR
                    )
                return True
            except (IndexError, ValueError):
                return False
        return False