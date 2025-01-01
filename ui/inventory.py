import pygame
from typing import List, Optional, Dict
from items.base_item import Item
from characters.base_character import Character

class Inventory:
    # Colors
    BG_COLOR = (32, 36, 44, 240)  # Dark background with slight transparency
    BORDER_COLOR = (64, 68, 76)
    INNER_BORDER_COLOR = (80, 84, 92)
    TEXT_COLOR = (240, 240, 240)  # Bright text
    SLOT_BG_COLOR = (48, 52, 64)  # Slightly lighter than background
    SLOT_BORDER_COLOR = (96, 100, 108)  # Lighter than normal border
    SLOT_HOVER_COLOR = (72, 76, 88)  # Lighter color for hover effect
    
    # Class-level cache for common surfaces
    _background_cache = {}
    _slot_cache = {}
    _cooldown_font = None
    
    def __init__(self, x: int, y: int, width: int = 280, height: int = 180):  # Reduced height and width
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 26)  # Slightly larger font
        self.title_font = pygame.font.Font(None, 32)  # Larger title font
        if not Inventory._cooldown_font:
            Inventory._cooldown_font = pygame.font.Font(None, 24)
        self.is_dragging = False
        self.drag_offset = (0, 0)
        
        # Create surfaces
        self.inventory_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Get or create cached background
        bg_key = (width, height)
        if bg_key not in Inventory._background_cache:
            background = pygame.Surface((width, height), pygame.SRCALPHA)
            background.fill(self.BG_COLOR)
            # Draw border
            pygame.draw.rect(background, self.BORDER_COLOR, background.get_rect(), width=2)
            Inventory._background_cache[bg_key] = background
        self.background = Inventory._background_cache[bg_key]
        
        # Pre-render title
        self.title_surface = self.title_font.render("Inventory", True, self.TEXT_COLOR)
        self.title_shadow = self.title_font.render("Inventory", True, (0, 0, 0))
        self.title_rect = self.title_surface.get_rect(x=10, y=5)
        
        # Inventory slots (2x3 grid)
        self.slot_size = 60  # Reduced slot size
        self.slot_padding = 8  # Reduced padding
        self.slots: List[Optional[Item]] = [None] * 6  # Now stores actual Item objects
        
        # Calculate grid layout
        self.grid_start_x = (width - (3 * self.slot_size + 2 * self.slot_padding)) // 2
        self.grid_start_y = 45  # Below title bar
        
        # Item interaction state
        self.hovered_slot = None
        self.selected_slot = None
        self.selected_item = None
        self.target_selection_mode = False
        
        # Get or create cached slot surfaces
        slot_key = self.slot_size
        if slot_key not in Inventory._slot_cache:
            normal_slot = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
            pygame.draw.rect(normal_slot, self.SLOT_BG_COLOR, normal_slot.get_rect(), border_radius=5)
            pygame.draw.rect(normal_slot, self.SLOT_BORDER_COLOR, normal_slot.get_rect(), width=2, border_radius=5)
            
            hover_slot = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
            pygame.draw.rect(hover_slot, self.SLOT_HOVER_COLOR, hover_slot.get_rect(), border_radius=5)
            pygame.draw.rect(hover_slot, self.SLOT_BORDER_COLOR, hover_slot.get_rect(), width=2, border_radius=5)
            
            Inventory._slot_cache[slot_key] = (normal_slot, hover_slot)
    
    def add_item(self, item: Item) -> bool:
        """Add an item to the inventory. Returns True if successful."""
        # First try to stack with existing items
        for i, slot_item in enumerate(self.slots):
            if slot_item is not None and slot_item.can_stack_with(item):
                # Try to add to this stack
                remainder = slot_item.add_to_stack(item.stack_count)
                if remainder == 0:
                    return True
                item.stack_count = remainder  # Update remaining count
        
        # If we get here, either couldn't stack or have remainder
        # Find first empty slot
        for i in range(len(self.slots)):
            if self.slots[i] is None:
                self.slots[i] = item
                return True
        return False
    
    def remove_item(self, slot_index: int, count: int = 1) -> Optional[Item]:
        """
        Remove items from the given slot.
        If removing all items or the last item, returns the item and clears the slot.
        If removing part of a stack, returns a new item with the removed count.
        """
        if not (0 <= slot_index < len(self.slots)) or self.slots[slot_index] is None:
            return None
        
        item = self.slots[slot_index]
        if count >= item.stack_count:
            # Remove entire stack
            self.slots[slot_index] = None
            return item
        
        # Remove partial stack
        new_item = item.split_stack(count)
        return new_item
    
    def get_slot_at_pos(self, pos: tuple[int, int]) -> Optional[int]:
        """Get the slot index at the given position relative to the inventory."""
        x, y = pos
        
        # Calculate grid position
        rel_x = x - self.grid_start_x
        rel_y = y - self.grid_start_y
        
        col = int(rel_x // (self.slot_size + self.slot_padding))
        row = int(rel_y // (self.slot_size + self.slot_padding))
        
        # Check if within valid slot bounds
        if col < 0 or col >= 3 or row < 0 or row >= 2:
            return None
        
        # Convert to slot index
        slot_index = row * 3 + col
        if slot_index < 0 or slot_index >= len(self.slots):
            return None
            
        # Calculate exact slot bounds
        slot_x = self.grid_start_x + col * (self.slot_size + self.slot_padding)
        slot_y = self.grid_start_y + row * (self.slot_size + self.slot_padding)
        
        # Check if click is within the slot's bounds
        if (slot_x <= x <= slot_x + self.slot_size and 
            slot_y <= y <= slot_y + self.slot_size):
            return slot_index
            
        return None
    
    def handle_event(self, event: pygame.event.Event):
        """Handle mouse events for the inventory."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.rect.collidepoint(event.pos):
                    # Check if clicking title bar
                    title_bar = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 35)
                    if title_bar.collidepoint(event.pos):
                        self.is_dragging = True
                        mouse_x, mouse_y = event.pos
                        self.drag_offset = (self.rect.x - mouse_x, self.rect.y - mouse_y)
                        return True  # Consume the event
                    else:
                        # Convert screen position to inventory-relative position
                        rel_mouse_pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
                        # Handle slot click
                        slot_index = self.get_slot_at_pos(rel_mouse_pos)
                        
                        # Debug print
                        print(f"Click at {rel_mouse_pos}, slot_index: {slot_index}")
                        
                        if slot_index is not None and self.slots[slot_index] is not None:
                            print(f"Selected item in slot {slot_index}: {self.slots[slot_index].name}")
                            self.selected_slot = slot_index
                            self.selected_item = self.slots[slot_index]
                            self.target_selection_mode = True
                            from engine.game_engine import GameEngine
                            if GameEngine.instance:
                                GameEngine.instance.game_state.targeting_item = True
                            return True  # Consume the event
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                was_dragging = self.is_dragging
                self.is_dragging = False
                return was_dragging  # Consume the event if we were dragging
        
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                mouse_x, mouse_y = event.pos
                self.rect.x = mouse_x + self.drag_offset[0]
                self.rect.y = mouse_y + self.drag_offset[1]
                
                # Keep within screen bounds
                screen = pygame.display.get_surface()
                self.rect.clamp_ip(screen.get_rect())
                return True  # Consume the event
            
            # Update hovered slot and item hover state
            if self.rect.collidepoint(event.pos):
                rel_mouse_pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
                self.hovered_slot = self.get_slot_at_pos(rel_mouse_pos)
                
                # Update item hover states
                for i, item in enumerate(self.slots):
                    if item is not None:
                        row = i // 3
                        col = i % 3
                        slot_x = self.grid_start_x + col * (self.slot_size + self.slot_padding)
                        slot_y = self.grid_start_y + row * (self.slot_size + self.slot_padding)
                        
                        # Update item position for tooltip
                        item.position = (self.rect.x + slot_x, self.rect.y + slot_y)
                        
                        # Check if mouse is over this slot
                        slot_rect = pygame.Rect(slot_x, slot_y, self.slot_size, self.slot_size)
                        item.is_hovered = slot_rect.collidepoint(rel_mouse_pos)
            else:
                self.hovered_slot = None
                # Clear all item hover states
                for item in self.slots:
                    if item is not None:
                        item.is_hovered = False
        
        return False
    
    def use_selected_item(self, target: Character) -> bool:
        """Use the selected item on the target. Returns True if successful."""
        if self.selected_item is None or self.selected_slot is None:
            print(f"[DEBUG] No item selected")  # Debug print
            return False
        
        # Get the user (first player character for now)
        from engine.game_engine import GameEngine
        if not GameEngine.instance:
            print(f"[DEBUG] No GameEngine instance")  # Debug print
            return False
        
        user = GameEngine.instance.stage_manager.player_characters[0]
        
        print(f"\n[DEBUG] Attempting to use item: {self.selected_item.name}")  # Debug print
        print(f"[DEBUG] User: {user.name}, Target: {target.name}")  # Debug print
        
        # Try to use the item
        if self.selected_item.use(user, target):
            print(f"[DEBUG] Item use successful, stack count: {self.selected_item.stack_count}")  # Debug print
            
            # First remove from RaidInventory if it exists
            if hasattr(GameEngine.instance, 'raid_inventory'):
                print(f"[DEBUG] Removing item from RaidInventory")  # Debug print
                # Remove from RaidInventory and save
                GameEngine.instance.raid_inventory.remove_item(self.selected_item.name)
                GameEngine.instance.raid_inventory.save_inventory()
                print(f"[DEBUG] RaidInventory updated and saved")  # Debug print
            
            # Then remove from UI inventory if stack is empty
            if self.selected_item.stack_count <= 0:
                print(f"[DEBUG] Stack empty, removing item from slot {self.selected_slot}")  # Debug print
                self.slots[self.selected_slot] = None
            
            # Finally sync UI inventory with RaidInventory
            if hasattr(GameEngine.instance, 'sync_inventory'):
                GameEngine.instance.sync_inventory()
                print(f"[DEBUG] UI inventory synced")  # Debug print
            
            # Reset selection state
            self.selected_item = None
            self.selected_slot = None
            self.target_selection_mode = False
            GameEngine.instance.game_state.targeting_item = False
            return True
        
        print(f"[DEBUG] Item use failed")  # Debug print
        return False
    
    def cancel_selection(self):
        """Cancel the current item selection"""
        self.selected_item = None
        self.selected_slot = None
        self.target_selection_mode = False
        from engine.game_engine import GameEngine
        if GameEngine.instance:
            GameEngine.instance.game_state.targeting_item = False
    
    def draw(self, screen: pygame.Surface):
        # Clear inventory surface
        self.inventory_surface.fill((0, 0, 0, 0))
        
        # Draw background
        screen.blit(self.background, self.rect)
        
        # Draw title with shadow
        screen.blit(self.title_shadow, (self.rect.x + 11, self.rect.y + 6))
        screen.blit(self.title_surface, (self.rect.x + 10, self.rect.y + 5))
        
        # Get cached slot surfaces
        normal_slot, hover_slot = Inventory._slot_cache[self.slot_size]
        
        # Draw inventory slots
        for i in range(6):
            row = i // 3
            col = i % 3
            
            slot_x = self.rect.x + self.grid_start_x + col * (self.slot_size + self.slot_padding)
            slot_y = self.rect.y + self.grid_start_y + row * (self.slot_size + self.slot_padding)
            
            # Draw slot background
            if i == self.hovered_slot:
                screen.blit(hover_slot, (slot_x, slot_y))
            else:
                screen.blit(normal_slot, (slot_x, slot_y))
            
            # Draw item icon if slot is not empty
            if self.slots[i]:
                # Calculate icon position (centered in slot)
                icon_x = slot_x + (self.slot_size - self.slots[i].icon.get_width()) // 2
                icon_y = slot_y + (self.slot_size - self.slots[i].icon.get_height()) // 2
                
                # Update item position for tooltip
                self.slots[i].position = (icon_x, icon_y)
                
                # Draw item icon
                screen.blit(self.slots[i].icon, (icon_x, icon_y))
                
                # Draw stack count if greater than 1
                if self.slots[i].stack_count > 1:
                    # Create stack count text with shadow
                    stack_text = str(self.slots[i].stack_count)
                    # Draw shadow
                    stack_shadow = Inventory._cooldown_font.render(stack_text, True, (0, 0, 0))
                    shadow_rect = stack_shadow.get_rect(bottomright=(slot_x + self.slot_size - 3, slot_y + self.slot_size - 3))
                    screen.blit(stack_shadow, shadow_rect)
                    # Draw text
                    stack_surface = Inventory._cooldown_font.render(stack_text, True, (255, 255, 255))
                    text_rect = stack_surface.get_rect(bottomright=(slot_x + self.slot_size - 4, slot_y + self.slot_size - 4))
                    screen.blit(stack_surface, text_rect)
                
                # Draw cooldown overlay if item is on cooldown
                if self.slots[i].current_cooldown > 0:
                    # Create semi-transparent black overlay
                    cooldown_surface = pygame.Surface((self.slot_size - 16, self.slot_size - 16), pygame.SRCALPHA)
                    cooldown_surface.fill((0, 0, 0, 128))  # Semi-transparent black
                    screen.blit(cooldown_surface, (icon_x, icon_y))
                    
                    # Draw cooldown number
                    cooldown_text = str(self.slots[i].current_cooldown)
                    # Draw shadow
                    cooldown_shadow = Inventory._cooldown_font.render(cooldown_text, True, (0, 0, 0))
                    shadow_rect = cooldown_shadow.get_rect(center=(icon_x + (self.slot_size - 16) // 2 + 1, icon_y + (self.slot_size - 16) // 2 + 1))
                    screen.blit(cooldown_shadow, shadow_rect)
                    # Draw text
                    cooldown_surface = Inventory._cooldown_font.render(cooldown_text, True, (255, 255, 255))
                    text_rect = cooldown_surface.get_rect(center=(icon_x + (self.slot_size - 16) // 2, icon_y + (self.slot_size - 16) // 2))
                    screen.blit(cooldown_surface, text_rect)
                
                # Draw tooltip if item is hovered
                if i == self.hovered_slot:
                    self.slots[i].is_hovered = True
                    self.slots[i].draw_tooltip(screen)
                else:
                    self.slots[i].is_hovered = False 