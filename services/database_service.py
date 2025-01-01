from typing import Dict, Any, Optional, List
from firebase_admin import db
from config.firebase_config import initialize_firebase
from config.login_config import LoginManager

class DatabaseService:
    def __init__(self):
        """Initialize the database service with Firebase."""
        print("Initializing DatabaseService...")  # Debug print
        initialize_firebase()  # Just initialize Firebase, don't store the reference
        # Get the user ID from credentials
        login_manager = LoginManager()
        credentials = login_manager.load_credentials()
        username = credentials[0] if credentials else None
        # TODO: Get actual user ID from Firebase Auth
        # For now, we'll look up the user ID from the username
        users_ref = db.reference('/users')
        users_data = users_ref.get()
        self.user_id = None
        if users_data and username:
            for uid, user_data in users_data.items():
                if user_data.get('username') == username:
                    self.user_id = uid
                    break
        if not self.user_id:
            raise ValueError(f"Could not find user ID for username: {username}")
        print(f"Initialized database service for user ID: {self.user_id}")  # Debug print
        
    def test_connection(self, player_id: str) -> bool:
        """Test the database connection by writing and reading a test value."""
        print(f"Testing connection for player: {player_id}")  # Debug print
        try:
            test_ref = db.reference(f'/users/{self.user_id}/test')
            test_data = {"test": "connection"}
            print(f"Writing test data to path: /users/{self.user_id}/test")  # Debug print
            test_ref.set(test_data)
            read_data = test_ref.get()
            print(f"Test write successful. Read data: {read_data}")
            test_ref.delete()
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False
            
    def save_player_data(self, player_id: str, data: Dict[str, Any]) -> None:
        """Save player data to Firebase."""
        print(f"Saving player data for: {player_id}")  # Debug print
        print(f"Data to save: {data}")  # Debug print
        try:
            if "RaidInventory" in data:
                # Save RaidInventory directly to maintain exact structure
                raid_ref = db.reference(f'/users/{self.user_id}/RaidInventory')
                raid_ref.set(data["RaidInventory"])
            else:
                ref = db.reference(f'/users/{self.user_id}')
                ref.set(data)
            print("Player data saved successfully")  # Debug print
        except Exception as e:
            print(f"Error saving player data: {e}")  # Debug print
            raise
    
    def get_player_data(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve player data from Firebase."""
        print(f"Getting player data for: {player_id}")  # Debug print
        try:
            ref = db.reference(f'/users/{self.user_id}')
            data = ref.get()
            print(f"Retrieved player data: {data}")  # Debug print
            return data if data else {}
        except Exception as e:
            print(f"Error getting player data: {e}")  # Debug print
            return {}
    
    def save_inventory(self, player_id: str, inventory_data: List[Dict[str, Any]]) -> None:
        """Save player's inventory to Firebase."""
        ref = db.reference(f'/users/{self.user_id}/inventory')
        ref.set(inventory_data)
    
    def get_inventory(self, player_id: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve player's inventory from Firebase."""
        ref = db.reference(f'/users/{self.user_id}/inventory')
        data = ref.get()
        return data if data else []
    
    def save_stage_progress(self, player_id: str, stage_data: Dict[str, Any]) -> None:
        """Save player's stage progress to Firebase."""
        ref = db.reference(f'/users/{self.user_id}/stages')
        ref.update(stage_data)
    
    def get_stage_progress(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve player's stage progress from Firebase."""
        ref = db.reference(f'/users/{self.user_id}/stages')
        data = ref.get()
        return data if data else {}
        
    def save_character_stats(self, player_id: str, character_id: str, stats: Dict[str, Any]) -> None:
        """Save character stats to Firebase."""
        ref = db.reference(f'/users/{self.user_id}/characters/{character_id}')
        ref.update(stats)
    
    def get_character_stats(self, player_id: str, character_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve character stats from Firebase."""
        ref = db.reference(f'/users/{self.user_id}/characters/{character_id}')
        data = ref.get()
        return data if data else {}
    
    def save_game_state(self, player_id: str, state: Dict[str, Any]) -> None:
        """Save the current game state to Firebase."""
        ref = db.reference(f'/game_states/{self.user_id}')
        ref.set(state)
    
    def get_game_state(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the game state from Firebase."""
        ref = db.reference(f'/game_states/{self.user_id}')
        data = ref.get()
        return data if data else {}
    
    def update_high_scores(self, player_id: str, score: int) -> None:
        """Update player's high score in Firebase."""
        ref = db.reference(f'/high_scores/{self.user_id}')
        current_score = ref.get() or 0
        if score > current_score:
            ref.set(score)
    
    def get_high_scores(self, limit: int = 10) -> Dict[str, int]:
        """Get top high scores from Firebase."""
        ref = db.reference('/high_scores')
        data = ref.order_by_value().limit_to_last(limit).get()
        return data if data else {} 