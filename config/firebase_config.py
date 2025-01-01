"""Firebase configuration and initialization."""
import firebase_admin
from firebase_admin import credentials, db
from pathlib import Path

def initialize_firebase():
    """Initialize Firebase with service account credentials."""
    print("Initializing Firebase...")  # Debug print
    
    # Path to service account key file
    cred_path = Path("config/serviceAccountKey.json")
    print(f"Looking for credentials at: {cred_path.absolute()}")  # Debug print
    
    if not cred_path.exists():
        raise FileNotFoundError(
            "Firebase service account key not found. Please download it from Firebase Console "
            "and save it as 'config/serviceAccountKey.json'"
        )
    
    # Initialize Firebase app if not already initialized
    if not firebase_admin._apps:
        print("Creating new Firebase app...")  # Debug print
        try:
            cred = credentials.Certificate(str(cred_path))
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://project-fighters-by-fishb0nes-default-rtdb.europe-west1.firebasedatabase.app/'
            })
            print("Firebase app created successfully")  # Debug print
        except Exception as e:
            print(f"Error initializing Firebase: {e}")  # Debug print
            raise
    else:
        print("Firebase app already initialized")  # Debug print
    
    # Test database connection
    try:
        db.reference('/')  # Just test if we can get a reference
        print("Successfully connected to database")  # Debug print
    except Exception as e:
        print(f"Error connecting to database: {e}")  # Debug print
        raise 