from dataclasses import dataclass
from typing import Callable, List, Optional
import time

@dataclass
class GameAction:
    """Represents a single game action with its callback and completion status."""
    callback: Callable
    is_completed: bool = False
    start_time: float = 0
    duration: float = 1.0  # Default 1 second duration

class ActionQueue:
    def __init__(self):
        self._queue: List[GameAction] = []
        self._current_action: Optional[GameAction] = None
    
    def add_action(self, callback: Callable, duration: float = 1.0):
        """Add a new action to the queue."""
        self._queue.append(GameAction(callback=callback, duration=duration))
    
    def clear(self):
        """Clear all pending actions."""
        self._queue.clear()
        self._current_action = None
    
    def update(self):
        """Update the action queue, executing actions when ready."""
        if not self._current_action and self._queue:
            # Start new action
            self._current_action = self._queue.pop(0)
            self._current_action.start_time = time.time()
            self._current_action.callback()
        
        elif self._current_action:
            # Check if current action is complete
            current_time = time.time()
            if current_time - self._current_action.start_time >= self._current_action.duration:
                self._current_action = None
    
    @property
    def is_busy(self) -> bool:
        """Check if there are any actions in progress or pending."""
        return bool(self._current_action or self._queue) 