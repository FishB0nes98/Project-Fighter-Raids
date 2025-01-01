import random
from typing import List, Type
from .modifier_base import Modifier, ModifierRarity
from .talent_modifiers import (
    HealingWave, BubbleBarrier, VialCarrier, Fishnet, CoralArmor, 
    IceCrystal, DeepSeaPressure, SpiritEssence, EssenceLink, CrystallineResonance,
    ArcaneMomentum, RapidGoldenArrows, AtlanteanWard, AncientAwakening, MermaidCrystal,
    AtlanteanHourglass, SwitchingSword
)

class ModifierManager:
    def __init__(self):
        self.available_modifiers: List[Type[Modifier]] = [
            HealingWave,
            BubbleBarrier,
            VialCarrier,
            Fishnet,
            CoralArmor,
            IceCrystal,
            DeepSeaPressure,
            SpiritEssence,
            EssenceLink,
            CrystallineResonance,
            ArcaneMomentum,
            RapidGoldenArrows,
            AtlanteanWard,
            AncientAwakening,
            MermaidCrystal,
            AtlanteanHourglass,
            SwitchingSword
        ]
        self.active_modifiers: List[Modifier] = []
        # Adjust weights to make rare modifiers more likely to appear
        self.rarity_weights = {
            ModifierRarity.COMMON: 0.35,     # Reduced
            ModifierRarity.UNCOMMON: 0.30,   # Same
            ModifierRarity.RARE: 0.20,       # Same
            ModifierRarity.EPIC: 0.10,       # Same
            ModifierRarity.LEGENDARY: 0.05   # New legendary weight
        }
        print("ModifierManager initialized with weights:", self.rarity_weights)
        
        # Map of modifier names to their classes
        self.modifier_map = {
            mod.__name__: mod for mod in self.available_modifiers
        }

    def get_random_modifiers(self, count: int = 3) -> List[Modifier]:
        """Get a list of random modifiers to choose from"""
        print(f"\nRequested {count} modifiers")
        print(f"Available modifier classes: {[mod.__name__ for mod in self.available_modifiers]}")
        
        # Get currently active modifier names from all stages
        from engine.game_engine import GameEngine
        active_modifier_names = set()
        if GameEngine.instance and hasattr(GameEngine.instance, 'raid_inventory'):
            for stage in range(1, 6):  # Check stages 1 through 5
                stage_modifiers = GameEngine.instance.raid_inventory.get_modifiers("atlantean_raid", stage)
                active_modifier_names.update(stage_modifiers)
        print(f"Currently active modifiers across all stages: {active_modifier_names}")
        
        # Filter out already active modifiers
        available_modifiers = [mod for mod in self.available_modifiers 
                             if mod.__name__ not in active_modifier_names]
        print(f"Available modifiers after filtering: {[mod.__name__ for mod in available_modifiers]}")
        
        # Create instances of available modifiers
        modifier_instances = [mod() for mod in available_modifiers]
        print(f"Created modifier instances: {[m.name for m in modifier_instances]}")
        
        # Ensure we have enough modifiers
        if len(modifier_instances) < count:
            print(f"Warning: Not enough modifiers available. Requested {count}, but only have {len(modifier_instances)}")
            return modifier_instances  # Return all available if we don't have enough
        
        # Weight modifiers by rarity
        weights = [self.rarity_weights[mod.rarity] for mod in modifier_instances]
        print(f"Weights by rarity: {list(zip([m.name for m in modifier_instances], weights))}")
        
        # Select random modifiers without replacement
        selected = []
        remaining_instances = modifier_instances.copy()
        remaining_weights = weights.copy()
        
        while len(selected) < count and remaining_instances:
            # Calculate total weight of remaining modifiers
            total_weight = sum(remaining_weights)
            if total_weight <= 0:
                print("Warning: Total weight is 0, breaking selection loop")
                break
                
            # Normalize weights
            normalized_weights = [w/total_weight for w in remaining_weights]
            print(f"\nSelection round {len(selected) + 1}:")
            print(f"Remaining modifiers: {[m.name for m in remaining_instances]}")
            print(f"Normalized weights: {list(zip([m.name for m in remaining_instances], normalized_weights))}")
            
            # Select one modifier
            chosen_idx = random.choices(range(len(remaining_instances)), weights=normalized_weights, k=1)[0]
            chosen_modifier = remaining_instances[chosen_idx]
            print(f"Selected: {chosen_modifier.name} (idx: {chosen_idx})")
            selected.append(chosen_modifier)
            
            # Remove chosen modifier from pool
            remaining_instances.pop(chosen_idx)
            remaining_weights.pop(chosen_idx)

        print(f"\nFinal selection: {[m.name for m in selected]}")
        return selected

    def activate_modifier(self, modifier: Modifier):
        """Activate a chosen modifier"""
        modifier.activate()
        self.active_modifiers.append(modifier)
        
        # Save to RaidInventory
        from engine.game_engine import GameEngine
        if GameEngine.instance and hasattr(GameEngine.instance, 'raid_inventory'):
            current_stage = GameEngine.instance.game_state.current_stage
            GameEngine.instance.raid_inventory.add_modifier(
                "atlantean_raid", 
                modifier.__class__.__name__,
                current_stage
            )

    def load_modifiers(self, game_state):
        """Load saved modifiers from RaidInventory"""
        if hasattr(game_state, 'raid_inventory'):
            # Clear existing modifiers
            self.active_modifiers = []
            
            print(f"\nLoading modifiers from all stages")
            loaded_any = False
            
            # Get current stage
            current_stage = game_state.stage_manager.current_stage_number if hasattr(game_state, 'stage_manager') else None
            print(f"Current stage: {current_stage}")
            
            # Load modifiers from all stages
            for stage in range(1, 6):  # Load from stages 1 through 5
                stage_modifiers = game_state.raid_inventory.get_modifiers("atlantean_raid", stage)
                print(f"Stage {stage} modifiers found: {stage_modifiers}")
                for modifier_name in stage_modifiers:
                    if modifier_name in self.modifier_map:
                        print(f"Creating Stage {stage} modifier: {modifier_name}")
                        modifier = self.modifier_map[modifier_name]()
                        modifier.activate()
                        self.active_modifiers.append(modifier)
                        loaded_any = True
            
            # If we're in stage 2 and no modifiers are selected for it yet, return False to trigger modifier selection
            if current_stage == 2 and not game_state.raid_inventory.get_modifiers("atlantean_raid", 2):
                print("In stage 2 with no modifiers selected yet, returning False to trigger selection")
                return False
            
            print(f"Total active modifiers after loading: {len(self.active_modifiers)}")
            for mod in self.active_modifiers:
                print(f"  - {mod.name} (active: {mod.is_active})")
                # Ensure all modifiers are properly activated
                if not mod.is_active:
                    print(f"  Activating {mod.name}")
                    mod.activate()
            
            return loaded_any  # Return True if any modifiers were loaded
        return False  # No modifiers to load

    def clear_modifiers(self, game_state):
        """Clear all active modifiers"""
        self.active_modifiers = []
        if hasattr(game_state, 'raid_inventory'):
            # Clear modifiers for all stages
            for stage in range(1, 6):  # Clear stages 1 through 5
                game_state.raid_inventory.clear_modifiers(
                    "atlantean_raid",
                    stage
                )

    def save_modifiers(self, game_state):
        """Save current modifiers to RaidInventory"""
        if hasattr(game_state, 'raid_inventory'):
            current_stage = game_state.stage_manager.current_stage_number
            # Save each active modifier
            for modifier in self.active_modifiers:
                game_state.raid_inventory.add_modifier(
                    "atlantean_raid",
                    modifier.__class__.__name__,
                    current_stage
                )

    def apply_turn_start(self, game_state):
        """Apply all active modifiers' turn start effects"""
        for modifier in self.active_modifiers:
            modifier.on_turn_start(game_state)

    def apply_turn_end(self, game_state):
        """Apply all active modifiers' turn end effects"""
        for modifier in self.active_modifiers:
            modifier.on_turn_end(game_state)

    def apply_battle_start(self, game_state):
        """Apply all active modifiers' battle start effects"""
        for modifier in self.active_modifiers:
            modifier.on_battle_start(game_state)

    def apply_battle_end(self, game_state):
        """Apply all active modifiers' battle end effects"""
        for modifier in self.active_modifiers:
            modifier.on_battle_end(game_state) 