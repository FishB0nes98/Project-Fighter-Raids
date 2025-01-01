"""Login configuration for auto-login functionality."""

import os
import json
import bcrypt
from pathlib import Path
from cryptography.fernet import Fernet

class LoginManager:
    def __init__(self):
        self.credentials_file = Path("config/credentials.enc")
        self.key_file = Path("config/key.key")
        self._init_encryption()
    
    def _init_encryption(self):
        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
        with open(self.key_file, "rb") as f:
            self.key = f.read()
        self.cipher = Fernet(self.key)
    
    def save_credentials(self, username: str, password: str):
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        data = {
            "username": username,
            "password": hashed.decode()
        }
        encrypted = self.cipher.encrypt(json.dumps(data).encode())
        with open(self.credentials_file, "wb") as f:
            f.write(encrypted)
    
    def load_credentials(self) -> tuple[str, str] | None:
        if not self.credentials_file.exists():
            return None
        try:
            with open(self.credentials_file, "rb") as f:
                encrypted = f.read()
            decrypted = self.cipher.decrypt(encrypted)
            data = json.loads(decrypted)
            return data["username"], data["password"]
        except:
            return None
    
    def verify_password(self, stored_hash: str, password: str) -> bool:
        return bcrypt.checkpw(password.encode(), stored_hash.encode()) 