"""
Machine profile management for saving and loading configurations.
"""

import json
import os
from datetime import datetime


class ProfileManager:
    """Manages machine profile storage and retrieval."""
    
    def __init__(self, profiles_dir="./profiles"):
        """
        Initialize profile manager.
        
        Args:
            profiles_dir: Directory to store profile files
        """
        self.profiles_dir = profiles_dir
        os.makedirs(profiles_dir, exist_ok=True)
    
    def save_profile(self, profile_name, config):
        """
        Save a machine configuration profile.
        
        Args:
            profile_name: Name for the profile
            config: Configuration dictionary to save
        """
        # Sanitize profile name
        safe_name = "".join(c for c in profile_name if c.isalnum() or c in ('-', '_'))
        if not safe_name:
            safe_name = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        filepath = os.path.join(self.profiles_dir, f"{safe_name}.json")
        
        profile_data = {
            "name": profile_name,
            "created": datetime.now().isoformat(),
            "config": config
        }
        
        with open(filepath, "w") as f:
            json.dump(profile_data, f, indent=2)
        
        return filepath
    
    def load_profile(self, profile_name):
        """
        Load a machine configuration profile.
        
        Args:
            profile_name: Name of the profile to load
            
        Returns:
            Configuration dictionary or None if not found
        """
        safe_name = "".join(c for c in profile_name if c.isalnum() or c in ('-', '_'))
        filepath = os.path.join(self.profiles_dir, f"{safe_name}.json")
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, "r") as f:
                profile_data = json.load(f)
            return profile_data.get("config")
        except Exception as e:
            print(f"Error loading profile: {e}")
            return None
    
    def list_profiles(self):
        """
        List all available profiles.
        
        Returns:
            List of profile names
        """
        profiles = []
        if os.path.exists(self.profiles_dir):
            for filename in os.listdir(self.profiles_dir):
                if filename.endswith(".json"):
                    profiles.append(filename[:-5])  # Remove .json extension
        return sorted(profiles)
    
    def delete_profile(self, profile_name):
        """
        Delete a machine configuration profile.
        
        Args:
            profile_name: Name of the profile to delete
            
        Returns:
            True if successful, False otherwise
        """
        safe_name = "".join(c for c in profile_name if c.isalnum() or c in ('-', '_'))
        filepath = os.path.join(self.profiles_dir, f"{safe_name}.json")
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            print(f"Error deleting profile: {e}")
        
        return False
