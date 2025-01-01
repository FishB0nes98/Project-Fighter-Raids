from .modifier_base import Modifier, ModifierRarity
import pygame
from characters.base_character import DamageText
import types  # For binding methods
import random  # For random selection

class HealingWave(Modifier):
    def __init__(self):
        super().__init__(
            name="Healing Wave",
            description="Restore 50HP to all living characters each turn",
            rarity=ModifierRarity.COMMON,
            image_path="assets/modifiers/healing_wave.png"
        )

    def on_turn_start(self, game_state):
        if self.is_active:
            for character in game_state.stage_manager.player_characters:
                if character.is_alive():  # Only heal living characters
                    character.heal(50)

class BubbleBarrier(Modifier):
    def __init__(self):
        super().__init__(
            name="Bubble Barrier",
            description="You start the game with bonus 700 currentHP",
            rarity=ModifierRarity.RARE,
            image_path="assets/modifiers/bubble_barrier.png"
        )

    def on_battle_start(self, game_state):
        if self.is_active:
            for character in game_state.stage_manager.player_characters:
                # Create a custom buff that provides bonus HP
                class BubbleBarrierBuff:
                    def __init__(self, icon_path):
                        self.type = "custom"
                        self.bonus_hp = 700
                        self.value = 700  # For display purposes
                        self.name = "Bubble Barrier"
                        self.description = "Bonus HP from Bubble Barrier"
                        self.duration = -1  # Permanent buff
                        self.heal_per_turn = 0
                        self.icon = pygame.image.load(icon_path) if icon_path else None
                    
                    def update(self):
                        """Return True to keep the buff active"""
                        return True  # Permanent buff, always return True
                
                # Add the buff and heal to full new max HP
                character.add_buff(BubbleBarrierBuff(self.image_path))
                character.heal(700)  # This will now work with the new heal method
                print(f"Added 700 HP to {character.name}, new HP: {character.stats.current_hp}")

class VialCarrier(Modifier):
    def __init__(self):
        super().__init__(
            name="Vial Carrier",
            description="Receive a Murky Water Vial at turn 2, 5, 10, 20 and 30",
            rarity=ModifierRarity.UNCOMMON,
            image_path="assets/modifiers/vial_carrier.png"
        )
        self.vial_turns = {2, 5, 10, 20, 30}  # Set of turns when vials are granted

    def on_turn_start(self, game_state):
        if self.is_active and game_state.game_state.turn_count in self.vial_turns:
            # Try to add Murky Water Vial to inventory
            for character in game_state.stage_manager.player_characters:
                if character.inventory and None in character.inventory.slots:  # Check for empty slot
                    from items.consumables import MurkyWaterVial
                    
                    # Create the vial item first
                    vial = MurkyWaterVial()
                    
                    # Add to RaidInventory first
                    if hasattr(game_state, 'raid_inventory'):
                        game_state.raid_inventory.add_item("Murky Water Vial", 1)
                        
                        # Clear both inventories
                        character.inventory.slots = [None] * 6
                        game_state.inventory.slots = [None] * 6
                        
                        # Repopulate both inventories from RaidInventory
                        game_state.raid_inventory.populate_ui_inventory(character.inventory)
                        game_state.raid_inventory.populate_ui_inventory(game_state.inventory)
                    else:
                        # Fallback to just adding to both UI inventories directly
                        character.inventory.add_item(vial)
                        game_state.inventory.add_item(vial)
                    
                    # Log the vial gain
                    game_state.battle_log.add_message(
                        f"Gained a Murky Water Vial! (Turn {game_state.game_state.turn_count})",
                        game_state.battle_log.BUFF_COLOR
                    )
                    break  # Only add one vial per turn 

class Fishnet(Modifier):
    def __init__(self):
        super().__init__(
            name="Fishnet",
            description="Start the battle with a Piranha companion that has tripled HP and attacks with you",
            rarity=ModifierRarity.UNCOMMON,
            image_path="assets/modifiers/fishnet.png"
        )
        self.piranha_spawned = False

    def on_battle_start(self, game_state):
        if self.is_active and not self.piranha_spawned:
            from characters.shadowfin_boss import Piranha
            
            # Create a Piranha companion
            piranha = Piranha()
            
            # Triple its HP
            piranha.stats.max_hp *= 3
            piranha.stats.current_hp = piranha.stats.max_hp
            
            # Add it to the player's team
            game_state.stage_manager.player_characters.append(piranha)
            
            # Modify player abilities to trigger piranha bite
            player = game_state.stage_manager.player_characters[0]
            for ability in player.abilities:
                original_use = ability.use
                def ability_with_bite_use(caster, targets, original_use=original_use, piranha=piranha):
                    result = original_use(caster, targets)
                    if result and piranha.is_alive():
                        # Use the piranha's bite ability
                        bite_ability = piranha.abilities[0]
                        # For auto-targeting abilities, we need to get the actual target
                        actual_targets = targets
                        if ability.auto_self_target:
                            # Find a valid target (first enemy that's not a piranha and is alive)
                            for enemy in game_state.stage_manager.current_stage.bosses:
                                if enemy.is_alive() and not isinstance(enemy, Piranha):
                                    actual_targets = [enemy]
                                    break
                        if actual_targets and actual_targets[0].is_alive() and not isinstance(actual_targets[0], Piranha):
                            # Create a floating text for the Piranha's attack
                            target = actual_targets[0]
                            damage = bite_ability.effects[0].value  # Get the bite damage value
                            # Position the text to the right of the target
                            text_x = target.position[0] + target.image.get_width() + 20
                            text_y = target.position[1] + target.image.get_height() // 2
                            damage_text = DamageText(
                                value=damage,
                                position=(text_x, text_y),
                                color=(255, 150, 150)  # Light red color for Piranha's attack
                            )
                            target.floating_texts.append(damage_text)
                            # Use the bite ability
                            bite_ability.use(piranha, actual_targets)
                    return result
                ability.use = ability_with_bite_use
            
            # Log the spawn
            game_state.battle_log.add_message(
                "A powerful Piranha joins your team!",
                game_state.battle_log.BUFF_COLOR
            )
            
            self.piranha_spawned = True 

class CoralArmor(Modifier):
    def __init__(self):
        super().__init__(
            name="Coral Armor",
            description="One of your random characters gain 8% armor",
            rarity=ModifierRarity.COMMON,
            image_path="assets/modifiers/coral_armor.png"
        )
        self.buff_applied = False

    def on_battle_start(self, game_state):
        if self.is_active and not self.buff_applied:
            import random
            
            # Get a random character from the player's team
            characters = game_state.stage_manager.player_characters
            if characters:
                target = random.choice(characters)
                
                # Create armor buff
                class CoralArmorBuff:
                    def __init__(self, icon_path):
                        self.type = "custom"
                        self.armor_bonus = 8
                        self.value = 8  # For display purposes
                        self.name = "Coral Armor"
                        self.description = "8% armor from Coral Armor"
                        self.duration = -1  # Permanent buff
                        self.heal_per_turn = 0
                        self.icon = pygame.image.load(icon_path) if icon_path else None
                    
                    def update(self):
                        """Return True to keep the buff active"""
                        return True  # Permanent buff
                
                # Add the buff to the character
                target.add_buff(CoralArmorBuff(self.image_path))
                target.stats.defense += 8
                
                # Log the buff application
                game_state.battle_log.add_message(
                    f"{target.name} is protected by Coral Armor!",
                    game_state.battle_log.BUFF_COLOR
                )
                
                self.buff_applied = True 

class IceCrystal(Modifier):
    # Class-level cache for frozen images
    _frozen_image_cache = {}
    
    def __init__(self):
        super().__init__(
            name="Ice Crystal",
            description="At game start, randomly freeze an enemy for 5 turns, disabling its abilities",
            rarity=ModifierRarity.EPIC,
            image_path="assets/modifiers/ice_crystal.png"
        )
        self.freeze_applied = False
    
    @staticmethod
    def get_frozen_image(original_image):
        """Get or create a frozen version of the image."""
        # Use image memory view as cache key
        key = original_image.get_view().raw
        
        if key not in IceCrystal._frozen_image_cache:
            # Create a copy of the original image
            frozen = original_image.copy()
            
            # Get image dimensions
            width = frozen.get_width()
            height = frozen.get_height()
            
            # Create ice effect by adding blue tint and crystalline overlay
            for x in range(width):
                for y in range(height):
                    r, g, b, a = frozen.get_at((x, y))
                    if a > 0:  # Only modify visible pixels
                        # Add blue tint
                        b = min(255, b + 50)
                        r = max(0, r - 30)
                        g = max(0, g - 10)
                        # Add crystalline effect
                        if (x + y) % 20 == 0:  # Create crystal pattern
                            r = min(255, r + 100)
                            g = min(255, g + 100)
                            b = min(255, b + 100)
                    frozen.set_at((x, y), (r, g, b, a))
            
            IceCrystal._frozen_image_cache[key] = frozen
        
        return IceCrystal._frozen_image_cache[key].copy()
    
    def on_battle_start(self, game_state):
        if self.is_active and not self.freeze_applied:
            import random
            
            # Get a random enemy
            enemies = game_state.stage_manager.current_stage.bosses
            if enemies:
                target = random.choice(enemies)
                
                # Create freeze effect
                class FrozenDebuff:
                    def __init__(self, icon_path):
                        self.type = "custom"
                        self.value = 5  # Duration display
                        self.name = "Frozen"
                        self.description = "Frozen solid! Cannot use abilities"
                        self.duration = 5
                        self.heal_per_turn = 0
                        self.icon = pygame.image.load(icon_path) if icon_path else None
                        
                        # Store original image and create frozen version
                        self.original_image = target.image
                        self.frozen_image = IceCrystal.get_frozen_image(self.original_image)
                        target.image = self.frozen_image
                        
                        # Store original ability use functions
                        self.original_abilities = [(ability, ability.use) for ability in target.abilities]
                        # Disable all abilities
                        for ability in target.abilities:
                            ability.use = lambda *args, **kwargs: False
                    
                    def update(self):
                        """Update the buff and return True if it should continue"""
                        self.duration -= 1
                        self.description = f"Frozen solid! Cannot use abilities\n{self.duration} turns remaining"
                        
                        if self.duration <= 0:
                            # Restore original image and abilities
                            target.image = self.original_image
                            for ability, original_use in self.original_abilities:
                                ability.use = original_use
                            return False
                        return True
                
                # Add the freeze debuff
                target.add_buff(FrozenDebuff(self.image_path))
                
                # Log the freeze
                game_state.battle_log.add_message(
                    f"{target.name} has been frozen solid!",
                    game_state.battle_log.BUFF_COLOR
                )
                
                self.freeze_applied = True 

class DeepSeaPressure(Modifier):
    def __init__(self):
        super().__init__(
            name="Deep Sea Pressure",
            description="Your characters gain 2% armor for each 10% HP they're missing",
            rarity=ModifierRarity.EPIC,
            image_path="assets/modifiers/deep_sea_pressure.png"
        )
        self.pressure_buffs = {}  # Track buffs per character

    def calculate_armor_bonus(self, character):
        """Calculate armor bonus based on missing HP percentage"""
        missing_hp_percent = ((character.stats.max_hp - character.stats.current_hp) / character.stats.max_hp) * 100
        return int(missing_hp_percent / 10) * 2  # 2% armor per 10% missing HP

    def on_turn_start(self, game_state):
        if self.is_active:
            for character in game_state.stage_manager.player_characters:
                if character.is_alive():
                    # Calculate new armor bonus
                    armor_bonus = self.calculate_armor_bonus(character)
                    
                    # Remove old buff if it exists
                    if character in self.pressure_buffs:
                        old_buff = self.pressure_buffs[character]
                        if old_buff in character.buffs:
                            character.buffs.remove(old_buff)
                            character.stats.defense -= old_buff.armor_bonus

                    # Create new pressure buff
                    class PressureBuff:
                        def __init__(self, armor_value, icon_path):
                            self.type = "custom"
                            self.armor_bonus = armor_value
                            self.value = armor_value  # For display purposes
                            self.name = "Deep Sea Pressure"
                            self.description = f"+{armor_value}% armor from Deep Sea Pressure"
                            self.duration = 1  # Refreshed each turn
                            self.heal_per_turn = 0
                            self.icon = pygame.image.load(icon_path) if icon_path else None
                        
                        def update(self):
                            """Return True to keep the buff active"""
                            self.duration -= 1
                            return self.duration > 0

                    # Apply new buff
                    new_buff = PressureBuff(armor_bonus, self.image_path)
                    character.add_buff(new_buff)
                    character.stats.defense += armor_bonus
                    self.pressure_buffs[character] = new_buff

                    # Log significant armor changes (optional)
                    if armor_bonus >= 5:  # Only log when getting significant armor
                        game_state.battle_log.add_message(
                            f"{character.name} gains {armor_bonus}% armor from Deep Sea Pressure!",
                            game_state.battle_log.BUFF_COLOR
                        ) 

class SpiritEssence(Modifier):
    def __init__(self):
        super().__init__(
            name="Spirit Essence",
            description="When you heal, gain 15% increased damage for 2 turns",
            rarity=ModifierRarity.RARE,
            image_path="assets/modifiers/spirit_essence.png"
        )
        self.essence_buffs = {}  # Track buffs per character
        
    def on_turn_start(self, game_state):
        if self.is_active:
            for character in game_state.stage_manager.player_characters:
                # Override heal method if not already overridden
                if not hasattr(character, 'original_heal'):
                    character.original_heal = character.heal
                    def heal_with_essence(amount: int) -> int:
                        healed = character.original_heal(amount)
                        if healed > 0:  # Only trigger if actual healing occurred
                            # Remove old buff if it exists
                            if character in self.essence_buffs:
                                old_buff = self.essence_buffs[character]
                                if old_buff in character.buffs:
                                    character.buffs.remove(old_buff)
                            
                            # Create new essence buff
                            class EssenceBuff:
                                def __init__(self, icon_path):
                                    self.type = "custom"
                                    self.value = 15  # 15% damage increase
                                    self.name = "Spirit Essence"
                                    self.description = "Damage increased by 15% from Spirit Essence"
                                    self.duration = 2  # 2 turns
                                    self.heal_per_turn = 0
                                    self.icon = pygame.image.load(icon_path) if icon_path else None
                                
                                def update(self):
                                    """Return True to keep the buff active"""
                                    self.duration -= 1
                                    self.description = f"Damage increased by 15% from Spirit Essence\n{self.duration} turns remaining"
                                    return self.duration > 0
                                
                                def apply_damage_increase(self, damage):
                                    """Increase damage by 15%"""
                                    return int(damage * 1.15)
                                
                                def on_hit_heal(self, damage):
                                    """Return healing amount based on damage dealt"""
                                    return int(damage * 0.15)  # Heal for 15% of damage dealt
                            
                            # Apply new buff
                            new_buff = EssenceBuff(self.image_path)
                            character.add_buff(new_buff)
                            self.essence_buffs[character] = new_buff
                            
                            # Log the buff application
                            game_state.battle_log.add_message(
                                f"{character.name} is empowered by Spirit Essence!",
                                game_state.battle_log.BUFF_COLOR
                            )
                        return healed
                    character.heal = heal_with_essence

class EssenceLink(Modifier):
    def __init__(self):
        super().__init__(
            name="Essence Link",
            description="When you use an ability that costs mana, heal for 15% of the mana spent",
            rarity=ModifierRarity.RARE,
            image_path="assets/modifiers/essence_link.png"
        )
        self.modified_abilities = {}  # Track modified abilities per character

    def on_turn_start(self, game_state):
        if self.is_active:
            for character in game_state.stage_manager.player_characters:
                # Modify each ability if not already modified
                for ability in character.abilities:
                    if ability not in self.modified_abilities:
                        original_use = ability.use
                        def use_with_essence_link(caster, targets, original_use=original_use, ability=ability):
                            # Call original use first
                            result = original_use(caster, targets)
                            
                            # If ability was used successfully and cost mana
                            if result and ability.mana_cost > 0:
                                # Calculate heal amount (15% of mana spent)
                                heal_amount = int(ability.mana_cost * 0.15)
                                if heal_amount > 0:
                                    # Heal the caster
                                    caster.heal(heal_amount)
                                    # Log the heal
                                    game_state.battle_log.add_message(
                                        f"Essence Link heals {caster.name} for {heal_amount} HP!",
                                        game_state.battle_log.HEAL_COLOR
                                    )
                            return result
                        
                        # Store and replace the ability's use function
                        self.modified_abilities[ability] = original_use
                        ability.use = use_with_essence_link 

class CrystallineResonance(Modifier):
    def __init__(self):
        super().__init__(
            name="Crystalline Resonance",
            description="Your abilities have a 20% chance to crystallize targets, making them take 25% more damage from the next ability that hits them",
            rarity=ModifierRarity.RARE,
            image_path="assets/modifiers/crystalline_resonance.png"
        )
        self.modified_abilities = {}  # Track modified abilities per character

    def on_turn_start(self, game_state):
        if self.is_active:
            for character in game_state.stage_manager.player_characters:
                # Modify each ability if not already modified
                for ability in character.abilities:
                    if ability not in self.modified_abilities:
                        original_use = ability.use
                        def use_with_crystallize(caster, targets, original_use=original_use):
                            # Call original use first
                            result = original_use(caster, targets)
                            
                            # If ability was used successfully
                            if result:
                                import random
                                
                                # For AoE abilities, get all valid targets
                                actual_targets = []
                                if any(effect.type == "damage_all" for effect in ability.effects):
                                    # Get all enemy targets
                                    if isinstance(caster, type(game_state.stage_manager.player_characters[0])):
                                        # Player casting, target all bosses
                                        from characters.shadowfin_boss import Piranha
                                        actual_targets = [boss for boss in game_state.stage_manager.current_stage.bosses 
                                                        if boss.is_alive() and not isinstance(boss, Piranha)]
                                    else:
                                        # Boss casting, target all players
                                        actual_targets = [char for char in game_state.stage_manager.player_characters 
                                                        if char.is_alive()]
                                else:
                                    # Single target ability
                                    actual_targets = targets if targets else []
                                
                                # 20% chance to crystallize each target
                                for target in actual_targets:
                                    if target.is_alive() and random.random() < 0.20:
                                        # Create crystallize buff
                                        class CrystallizeBuff:
                                            def __init__(self, icon_path):
                                                self.type = "custom"
                                                self.value = 25  # 25% increased damage
                                                self.name = "Crystallized"
                                                self.description = "Takes 25% more damage from the next ability"
                                                self.duration = -1  # Will be removed after taking damage
                                                self.heal_per_turn = 0
                                                self.icon = pygame.image.load(icon_path) if icon_path else None
                                                self.triggered = False
                                            
                                            def update(self):
                                                """Return True to keep the buff active"""
                                                return not self.triggered
                                            
                                            def apply_damage_taken_increase(self, damage):
                                                """Increase damage taken by 25% and mark as triggered"""
                                                self.triggered = True
                                                return int(damage * 1.25)
                                            
                                            def on_damage_taken(self, damage):
                                                """Called when the target takes damage"""
                                                increased_damage = self.apply_damage_taken_increase(damage)
                                                # Log the bonus damage
                                                game_state.battle_log.add_message(
                                                    f"Crystallize shatters! +{increased_damage - damage} bonus damage!",
                                                    game_state.battle_log.DAMAGE_COLOR
                                                )
                                                # Safely remove the buff
                                                if self in target.buffs:
                                                    target.buffs.remove(self)
                                                return increased_damage
                                        
                                        # Remove any existing crystallize
                                        target.buffs = [b for b in target.buffs if not isinstance(b, CrystallizeBuff)]
                                        # Add new crystallize
                                        target.add_buff(CrystallizeBuff(self.image_path))
                                        # Log the crystallize
                                        game_state.battle_log.add_message(
                                            f"{target.name} has been crystallized!",
                                            game_state.battle_log.BUFF_COLOR
                                        )
                            return result
                        
                        # Store and replace the ability's use function
                        self.modified_abilities[ability] = original_use
                        ability.use = use_with_crystallize 

class ArcaneMomentum(Modifier):
    def __init__(self):
        super().__init__(
            name="Arcane Momentum",
            description="Whenever you cast an ability, there is 35% chance/ability to be reduced (the active cooldown) by 1 turn",
            rarity=ModifierRarity.RARE,
            image_path="assets/modifiers/arcane_momentum.png"
        )
        self.modified_abilities = {}  # Track modified abilities per character

    def on_turn_start(self, game_state):
        if self.is_active:
            for character in game_state.stage_manager.player_characters:
                # Modify each ability if not already modified
                for ability in character.abilities:
                    if ability not in self.modified_abilities:
                        original_use = ability.use
                        def use_with_momentum(caster, targets, original_use=original_use):
                            # Call original use first
                            result = original_use(caster, targets)
                            
                            # If ability was used successfully
                            if result:
                                import random
                                
                                # Check each ability for cooldown reduction (35% chance)
                                for other_ability in caster.abilities:
                                    if other_ability.current_cooldown > 0 and random.random() < 0.35:
                                        # Reduce cooldown by 1
                                        other_ability.current_cooldown = max(0, other_ability.current_cooldown - 1)
                                        # Log the cooldown reduction
                                        game_state.battle_log.add_message(
                                            f"Arcane Momentum reduces {other_ability.name}'s cooldown by 1!",
                                            game_state.battle_log.BUFF_COLOR
                                        )
                            return result
                        
                        # Store and replace the ability's use function
                        self.modified_abilities[ability] = original_use
                        ability.use = use_with_momentum 

class RapidGoldenArrows(Modifier):
    def __init__(self):
        super().__init__(
            name="Rapid Golden Arrows",
            description="After each hit of an ability, fire a golden arrow at the same target dealing 50% of Kagome's Golden Arrow damage.",
            rarity=ModifierRarity.EPIC,
            image_path="assets/modifiers/rapid_golden_arrows.png"
        )
        self.original_ability_uses = {}  # Store original ability use methods
        self.original_execute_hits = {}  # Store original execute_hit methods
        self.golden_arrow_damage = 345  # Kagome's Golden Arrow base damage
        self.processed_characters = set()  # Track which characters we've processed
        print("\nRapidGoldenArrows initialized")

    def bind_character_abilities(self, char, game_engine):
        """Bind abilities for a single character"""
        print(f"\nBinding abilities for character: {char.name}")
        for ability in char.abilities:
            print(f"Processing ability: {ability.name}")
            ability_id = id(ability)  # Use object's id as dictionary key
            if ability_id not in self.original_ability_uses:
                print(f"Storing original methods for ability: {ability.name}")
                self.original_ability_uses[ability_id] = ability.use
                
                # For multi-hit abilities like Christie's Q
                if hasattr(ability, 'execute_hit'):
                    print(f"Found multi-hit ability: {ability.name}")
                    self.original_execute_hits[ability_id] = ability.execute_hit
                    
                    def create_modified_execute_hit(original_execute_hit, ability):
                        def modified_execute_hit(self_ability):
                            print(f"\nExecuting modified execute_hit for {ability.name}")
                            # Call original execute_hit first
                            original_execute_hit()  # Don't pass any arguments, it's already bound
                            
                            # Fire golden arrow after each hit
                            if ability.current_targets:
                                print("Firing golden arrow after hit")
                                self.fire_golden_arrow(ability.caster, ability.current_targets[0])
                        return modified_execute_hit
                    
                    # Create and bind the modified execute_hit method
                    print(f"Binding modified execute_hit to {ability.name}")
                    modified_execute_hit = create_modified_execute_hit(ability.execute_hit, ability)
                    ability.execute_hit = types.MethodType(modified_execute_hit, ability)
                    print("Modified execute_hit bound successfully")
                
                # For regular abilities
                def create_modified_use(original_use, ability):
                    def modified_use(caster, targets):
                        print(f"\nExecuting modified use for {ability.name}")
                        # Call original use first
                        result = original_use(caster, targets)
                        if result and targets:  # Only proceed if ability was used successfully
                            print("Original ability use successful")
                            # Check if ability has damage effects or is a custom damage ability
                            has_damage = False
                            for effect in ability.effects:
                                if effect.type in ["damage", "damage_all"]:
                                    has_damage = True
                                    break
                            
                            # Also check if it's a custom damage ability (like Christie's W)
                            if not has_damage and hasattr(ability, 'name'):
                                damage_ability_names = ["Slamba Slam", "Throwkick", "Golden Arrow", "Golden Arrow Storm", "Ghostly Scream"]
                                if ability.name in damage_ability_names:
                                    has_damage = True
                            
                            # Fire golden arrow if ability deals damage
                            if has_damage and not hasattr(ability, 'execute_hit'):  # Skip multi-hit abilities here
                                print("Firing golden arrow")
                                self.fire_golden_arrow(caster, targets[0])
                        return result
                    return modified_use
                
                print(f"Binding modified use to {ability.name}")
                ability.use = create_modified_use(self.original_ability_uses[ability_id], ability)
                print("Modified use bound successfully")

    def on_battle_start(self, game_engine):
        print("\nRapidGoldenArrows.on_battle_start called")
        # Process all current characters
        for char in game_engine.stage_manager.player_characters:
            self.bind_character_abilities(char, game_engine)
            self.processed_characters.add(id(char))

    def on_turn_start(self, game_engine):
        """Check for new characters at the start of each turn"""
        if self.is_active:
            print("\nRapidGoldenArrows.on_turn_start called")
            # Check for new characters
            for char in game_engine.stage_manager.player_characters:
                if id(char) not in self.processed_characters:
                    print(f"Found new character: {char.name}")
                    self.bind_character_abilities(char, game_engine)
                    self.processed_characters.add(id(char))

    def fire_golden_arrow(self, caster, target):
        print(f"\nFiring golden arrow from {caster.name} to {target.name}")
        # Calculate start and end positions
        start_x = caster.position[0] + caster.image.get_width() // 2
        start_y = caster.position[1] + caster.image.get_height() // 2
        end_x = target.position[0] + target.image.get_width() // 2
        end_y = target.position[1] + target.image.get_height() // 2
        
        # Create arrow visual effect
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            arrow = GameEngine.instance.visual_effects.create_projectile(
                start_pos=(start_x, start_y),
                end_pos=(end_x, end_y),
                color=(255, 215, 0),  # Golden color
                duration=0.5,
                size=15,
                trail_length=8
            )
            GameEngine.instance.visual_effects.add_effect(arrow)
            print("Created arrow visual effect")
            
            # Apply 50% of Kagome's Golden Arrow damage
            damage = self.golden_arrow_damage * 0.5
            # Apply damage increase from caster's buffs
            for buff in caster.buffs:
                if hasattr(buff, 'apply_damage_increase'):
                    damage = buff.apply_damage_increase(damage)
            target.take_damage(int(damage))
            print(f"Dealt {int(damage)} damage")
            
            # Log the effect
            GameEngine.instance.battle_log.add_message(
                f"Rapid Golden Arrow deals {int(damage)} damage!",
                GameEngine.instance.battle_log.DAMAGE_COLOR
            )
            print("Added battle log message")

    def on_battle_end(self, game_engine):
        print("\nRapidGoldenArrows.on_battle_end called")
        # Restore original ability use methods
        for char in game_engine.stage_manager.player_characters:
            print(f"Restoring methods for character: {char.name}")
            for ability in char.abilities:
                ability_id = id(ability)
                if ability_id in self.original_ability_uses:
                    print(f"Restoring original use for {ability.name}")
                    ability.use = self.original_ability_uses[ability_id]
                # Restore original execute_hit if it exists
                if ability_id in self.original_execute_hits:
                    print(f"Restoring original execute_hit for {ability.name}")
                    ability.execute_hit = self.original_execute_hits[ability_id]
        self.original_ability_uses.clear()
        self.original_execute_hits.clear()
        self.processed_characters.clear()  # Clear processed characters list
        print("Cleared stored methods") 

class AtlanteanWard(Modifier):
    def __init__(self):
        super().__init__(
            name="Atlantean Ward",
            description="Characters gain 0.5% armor each turn from ancient Atlantean protection",
            rarity=ModifierRarity.UNCOMMON,
            image_path="assets/modifiers/atlantean_ward.png"
        )
        self.armor_buffs = {}  # Track buffs per character

    def on_turn_start(self, game_state):
        if self.is_active:
            for character in game_state.stage_manager.player_characters:
                if character.is_alive():
                    # Remove old buff if it exists
                    if character in self.armor_buffs:
                        old_buff = self.armor_buffs[character]
                        if old_buff in character.buffs:
                            character.buffs.remove(old_buff)
                            
                    # Calculate new total armor bonus
                    current_bonus = 0.5
                    if character in self.armor_buffs:
                        current_bonus = self.armor_buffs[character].armor_bonus + 0.5

                    class AtlanteanWardBuff:
                        def __init__(self, icon_path):
                            self.type = "custom"
                            self.armor_bonus = current_bonus
                            self.value = current_bonus  # For display purposes
                            self.name = "Atlantean Ward"
                            self.description = f"Total of {current_bonus:.2f}% armor from Atlantean Ward"
                            self.duration = -1  # Permanent buff
                            self.heal_per_turn = 0
                            self.icon = pygame.image.load(icon_path) if icon_path else None
                        
                        def update(self):
                            """Return True to keep the buff active"""
                            return True  # Permanent buff
                    
                    # Add the buff to the character
                    new_buff = AtlanteanWardBuff(self.image_path)
                    character.add_buff(new_buff)
                    character.stats.defense += 0.5
                    self.armor_buffs[character] = new_buff
                    
                    # Log the buff application
                    game_state.battle_log.add_message(
                        f"{character.name} gains armor from Atlantean Ward (Total: {current_bonus:.2f}%)!",
                        game_state.battle_log.BUFF_COLOR
                    ) 

class AncientAwakening(Modifier):
    def __init__(self):
        super().__init__(
            name="Ancient Awakening",
            description="One of your random characters awakens their ancient power, gaining double maximum mana",
            rarity=ModifierRarity.LEGENDARY,
            image_path="assets/modifiers/ancient_awakening.png"
        )
        self.buff_applied = False
        self.excluded_types = {"Piranha", "FrozenWarrior"}  # Types to exclude

    def on_battle_start(self, game_state):
        if self.is_active and not self.buff_applied:
            import random
            
            # Get eligible characters (exclude special allies)
            eligible_characters = [
                char for char in game_state.stage_manager.player_characters 
                if char.is_alive() and type(char).__name__ not in self.excluded_types
            ]
            
            if eligible_characters:
                target = random.choice(eligible_characters)
                
                # Create mana buff
                class AncientAwakeningBuff:
                    def __init__(self, icon_path):
                        self.type = "custom"
                        self.mana_multiplier = 2
                        self.value = 2  # For display purposes
                        self.name = "Ancient Awakening"
                        self.description = "Maximum mana doubled by Ancient Awakening"
                        self.duration = -1  # Permanent buff
                        self.heal_per_turn = 0
                        self.icon = pygame.image.load(icon_path) if icon_path else None
                    
                    def update(self):
                        """Return True to keep the buff active"""
                        return True  # Permanent buff
                
                # Add the buff to the character
                target.add_buff(AncientAwakeningBuff(self.image_path))
                
                # Double max mana and restore to full
                target.stats.max_mana *= 2
                target.stats.current_mana = target.stats.max_mana
                
                # Log the buff application
                game_state.battle_log.add_message(
                    f"{target.name} awakens their ancient power, doubling their mana!",
                    game_state.battle_log.BUFF_COLOR
                )
                
                self.buff_applied = True 

class MermaidCrystal(Modifier):
    def __init__(self):
        super().__init__(
            name="Mermaid Crystal",
            description="At turn 10,20,25,35,45 and every 10 turns after, enchants one random ability, making it cost no mana and deal 20% more damage for 5 turns",
            rarity=ModifierRarity.EPIC,
            image_path="assets/modifiers/mermaid_crystal.png"
        )
        # Store the turns when enchantment should occur
        self.enchant_turns = {9, 19, 24, 34, 44}  # Adjusted for 0-based turn count
        # Add turns beyond 45 up to a reasonable limit
        for turn in range(54, 200, 10):  # Adjusted for 0-based turn count
            self.enchant_turns.add(turn)
        self.original_ability_uses = {}  # Track original ability use methods by ability_id
        self.current_buffs = {}  # Track active buffs per character
        print("MermaidCrystal initialized with turns:", sorted(list(self.enchant_turns)))

    def get_original_use(self, ability):
        """Get the most base-level original use method"""
        if hasattr(ability, '_base_use'):
            return ability._base_use
        return ability.use

    def store_original_use(self, ability):
        """Store the original use method and ensure we have the base one"""
        ability_id = id(ability)
        if not hasattr(ability, '_base_use'):
            ability._base_use = ability.use
        if ability_id not in self.original_ability_uses:
            self.original_ability_uses[ability_id] = ability.use
        return ability_id

    def restore_ability(self, ability):
        """Restore ability to its original state"""
        ability_id = id(ability)
        if hasattr(ability, '_base_use'):
            ability.use = ability._base_use
        elif ability_id in self.original_ability_uses:
            ability.use = self.original_ability_uses[ability_id]

    def on_turn_start(self, game_state):
        current_turn = game_state.game_state.turn_count - 1  # Convert to 0-based
        if self.is_active and current_turn in self.enchant_turns:
            print(f"\nMermaidCrystal activating on turn {current_turn + 1}")
            import random
            
            # Get all eligible characters (excluding special allies)
            eligible_characters = [
                char for char in game_state.stage_manager.player_characters 
                if char.is_alive() and not any(t in type(char).__name__ for t in ["Piranha", "FrozenWarrior"])
            ]
            print(f"Eligible characters: {[char.name for char in eligible_characters]}")
            
            if eligible_characters:
                # Select one random character
                target_char = random.choice(eligible_characters)
                print(f"Selected character: {target_char.name}")
                
                # Get all abilities that can deal damage
                eligible_abilities = []
                for ability in target_char.abilities:
                    has_damage = False
                    # Check for damage effects
                    for effect in ability.effects:
                        if effect.type in ["damage", "damage_all"]:
                            has_damage = True
                            break
                    # Also check if it's a custom damage ability
                    if not has_damage and hasattr(ability, 'name'):
                        damage_ability_names = ["Slamba Slam", "Throwkick", "Golden Arrow", "Golden Arrow Storm", "Ghostly Scream"]
                        if ability.name in damage_ability_names:
                            has_damage = True
                    if has_damage:
                        eligible_abilities.append(ability)
                print(f"Eligible abilities: {[ability.name for ability in eligible_abilities]}")
                
                if eligible_abilities:
                    # Select one random ability
                    target_ability = random.choice(eligible_abilities)
                    print(f"Selected ability: {target_ability.name}")
                    
                    # Remove old enchantment if it exists
                    if target_char in self.current_buffs:
                        old_buff = self.current_buffs[target_char]
                        if old_buff in target_char.buffs:
                            target_char.buffs.remove(old_buff)
                            print(f"Removed old buff from {target_char.name}")
                    
                    # Store original ability use method
                    ability_id = self.store_original_use(target_ability)
                    print(f"Stored original use method for {target_ability.name}")
                    
                    # Create enchantment buff
                    class MermaidCrystalBuff:
                        def __init__(self, ability_name, icon_path):
                            self.type = "custom"
                            self.value = 5  # Duration display
                            self.name = "Mermaid Crystal Enchantment"
                            self.description = f"{ability_name} is enchanted:\n• Costs no mana\n• Deals 20% more damage\n{self.value} turns remaining"
                            self.duration = 5
                            self.heal_per_turn = 0
                            self.ability_name = ability_name
                            self.ability_id = ability_id  # Store ability_id for reference
                            self.icon = pygame.image.load(icon_path) if icon_path else None
                        
                        def update(self):
                            """Update the buff and return True if it should continue"""
                            self.duration -= 1
                            self.value = self.duration
                            self.description = f"{self.ability_name} is enchanted:\n• Costs no mana\n• Deals 20% more damage\n{self.duration} turns remaining"
                            return self.duration > 0
                    
                    # Create and add the buff
                    new_buff = MermaidCrystalBuff(target_ability.name, self.image_path)
                    target_char.add_buff(new_buff)
                    self.current_buffs[target_char] = new_buff
                    print(f"Added new buff to {target_char.name}")
                    
                    # Create enchanted version of the ability
                    def enchanted_use(caster, targets):
                        print(f"\nExecuting enchanted {target_ability.name}")
                        # Store original mana cost
                        original_mana_cost = target_ability.mana_cost
                        target_ability.mana_cost = 0
                        
                        # Call original use
                        original_use = self.get_original_use(target_ability)
                        result = original_use(caster, targets)
                        
                        # If the ability was used successfully and deals damage
                        if result:
                            print(f"Ability used successfully, applying damage boost")
                            # For abilities with damage effects
                            for effect in target_ability.effects:
                                if effect.type in ["damage", "damage_all"]:
                                    original_value = effect.value
                                    effect.value = int(effect.value * 1.2)  # 20% more damage
                                    print(f"Boosted damage from {original_value} to {effect.value}")
                                    # Use the ability with boosted damage
                                    result = True
                                    # Restore original damage
                                    effect.value = original_value
                        
                        # Restore original mana cost
                        target_ability.mana_cost = original_mana_cost
                        return result
                    
                    # Apply the enchanted version
                    target_ability.use = enchanted_use
                    print(f"Applied enchanted version to {target_ability.name}")
                    
                    # Log the enchantment
                    game_state.battle_log.add_message(
                        f"Mermaid Crystal enchants {target_char.name}'s {target_ability.name}!",
                        game_state.battle_log.BUFF_COLOR
                    )
    
    def on_turn_end(self, game_state):
        """Check for expired buffs and restore original abilities"""
        if self.is_active:
            print("\nMermaidCrystal.on_turn_end checking buffs")
            for char in list(self.current_buffs.keys()):
                buff = self.current_buffs[char]
                if buff not in char.buffs:  # Buff has expired
                    print(f"Buff expired for {char.name}")
                    # Find the ability with this buff's ability_id and restore it
                    for ability in char.abilities:
                        if id(ability) == buff.ability_id:
                            print(f"Restoring original use for {ability.name}")
                            self.restore_ability(ability)
                            if buff.ability_id in self.original_ability_uses:
                                del self.original_ability_uses[buff.ability_id]
                    del self.current_buffs[char]
    
    def on_battle_end(self, game_state):
        """Clean up and restore all original abilities"""
        if self.is_active:
            print("\nMermaidCrystal.on_battle_end called")
            # Restore all original abilities
            for char in game_state.stage_manager.player_characters:
                print(f"Checking abilities for {char.name}")
                for ability in char.abilities:
                    if id(ability) in self.original_ability_uses:
                        print(f"Restoring original use for {ability.name}")
                        self.restore_ability(ability)
            self.original_ability_uses.clear()
            self.current_buffs.clear()
            print("Cleared stored methods") 

class AtlanteanHourglass(Modifier):
    def __init__(self):
        super().__init__(
            name="Atlantean Hourglass",
            description="Places an Atlantean Hourglass debuff on a random enemy that explodes after 10 turns, dealing 3700 HP damage",
            rarity=ModifierRarity.RARE,
            image_path="assets/modifiers/atlantean_hourglass.png"
        )
        self.hourglass_applied = False

    def on_battle_start(self, game_state):
        if self.is_active and not self.hourglass_applied:
            import random
            
            # Get a random enemy
            enemies = game_state.stage_manager.current_stage.bosses
            if enemies:
                target = random.choice(enemies)
                
                # Create a custom debuff that tracks turns and explodes
                class HourglassDebuff:
                    def __init__(self, icon_path):
                        self.type = "debuff"
                        self.name = "Atlantean Hourglass"
                        self.description = "After 10 turns, this hourglass will explode dealing 3700 HP damage"
                        self.duration = 10
                        self.value = 3700  # Show the damage value in tooltip instead of duration
                        self.icon = pygame.image.load(icon_path) if icon_path else None
                        self.target = target
                    
                    def update(self):
                        """Return True to keep the debuff active"""
                        self.duration -= 1
                        self.description = f"After {self.duration} turns, this hourglass will explode dealing 3700 HP damage"
                        if self.duration <= 0:
                            # Deal damage when the hourglass expires
                            damage = 3700
                            self.target.take_damage(damage)
                            # Create damage text using position instead of rect
                            DamageText(self.target.position[0] + self.target.image.get_width() // 2,
                                     self.target.position[1],
                                     str(damage), (255, 0, 0))
                            return False
                        return True
                
                # Add the hourglass debuff
                target.add_buff(HourglassDebuff(self.image_path))
                
                # Log the application
                game_state.battle_log.add_message(
                    f"An Atlantean Hourglass appears above {target.name}!",
                    game_state.battle_log.BUFF_COLOR
                )
                
                self.hourglass_applied = True 

class SwitchingSword(Modifier):
    def __init__(self):
        super().__init__(
            name="Switching Sword",
            description="Randomly placed on an ally at game start. Alternates between +15% and -15% damage each turn.",
            rarity=ModifierRarity.COMMON,
            image_path="assets/modifiers/switching_sword.png"
        )
        self.buff_applied = False
        self.current_turn_positive = True
        self.buffed_character = None

    def on_battle_start(self, game_state):
        if self.is_active and not self.buff_applied:
            # Get all valid characters
            valid_characters = [char for char in game_state.stage_manager.player_characters 
                              if char.is_alive()]
            
            if valid_characters:
                # Randomly select a character
                self.buffed_character = random.choice(valid_characters)
                self.buff_applied = True
                print(f"Switching Sword applied to {self.buffed_character.name}")
                
                # Apply initial positive buff
                self.current_turn_positive = True
                self.apply_damage_modifier(game_state)

    def on_turn_start(self, game_state):
        if self.is_active and self.buffed_character and self.buffed_character.is_alive():
            # Toggle the buff between positive and negative
            self.current_turn_positive = not self.current_turn_positive
            self.apply_damage_modifier(game_state)

    def apply_damage_modifier(self, game_state):
        if self.buffed_character:
            # Remove any existing Switching Sword buff
            self.buffed_character.buffs = [buff for buff in self.buffed_character.buffs 
                                         if not hasattr(buff, 'is_switching_sword')]
            
            # Create new buff
            class SwitchingSwordBuff:
                def __init__(self, is_positive, icon_path):
                    self.type = "custom"
                    self.is_switching_sword = True  # Mark this as our buff
                    self.value = 15 if is_positive else -15  # For display purposes
                    self.name = "Switching Sword"
                    self.description = f"{'Increased' if is_positive else 'Decreased'} damage by 15%"
                    self.duration = 1  # Lasts until next turn
                    self.heal_per_turn = 0
                    self.icon = pygame.image.load(icon_path) if icon_path else None
                    self.is_positive = is_positive
                
                def update(self):
                    """Return True to keep the buff active"""
                    self.duration -= 1
                    return self.duration > 0
                
                def apply_damage_increase(self, damage):
                    """Modify damage based on current state"""
                    return int(damage * (1.15 if self.is_positive else 0.85))
            
            # Add the new buff
            new_buff = SwitchingSwordBuff(self.current_turn_positive, self.image_path)
            self.buffed_character.add_buff(new_buff)
            
            # Create floating text to show the effect
            buff_text = f"+15% DMG" if self.current_turn_positive else "-15% DMG"
            DamageText(
                self.buffed_character.position[0] + self.buffed_character.image.get_width() // 2,
                self.buffed_character.position[1],
                buff_text,
                (0, 255, 0) if self.current_turn_positive else (255, 0, 0)
            )
            
            # Log the buff application
            game_state.battle_log.add_message(
                f"Switching Sword {'empowers' if self.current_turn_positive else 'weakens'} {self.buffed_character.name}!",
                game_state.battle_log.BUFF_COLOR
            ) 