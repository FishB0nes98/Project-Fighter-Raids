from items.base_item import Item

class ShadowEssence(Item):
    def __init__(self):
        super().__init__(
            name="Shadow Essence",
            description="A mysterious dark essence extracted from a Shadow Assassin. Used in crafting.",
            rarity="Rare",
            item_type="Material",
            icon_path="assets/items/shadow_essence.png",
            max_stack=10
        )
        self.is_consumable = False
        
    def use(self, user, target) -> bool:
        """Cannot be used directly"""
        return False 

class LeviathanScale(Item):
    def __init__(self):
        super().__init__(
            name="Leviathan Scale",
            description="A massive, iridescent scale from the Dark Leviathan. Used in crafting powerful water-based equipment.",
            rarity="Rare",
            item_type="Material",
            icon_path="assets/items/leviathan_scale.png",
            max_stack=10
        )
        self.is_consumable = False
        
    def use(self, user, target) -> bool:
        """Cannot be used directly"""
        return False 