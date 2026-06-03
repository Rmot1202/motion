"""Persist and retrieve furnace dashboard profiles."""

import json
import os
from datetime import datetime


class ProfileManager:
    """Manage JSON profile storage and retrieval.

    Attributes:
        profiles_dir (str): Directory that stores profile JSON files.
    """

    def __init__(self, profiles_dir="./profiles"):
        """Create the manager and ensure the profile directory exists."""

        self.profiles_dir = profiles_dir
        os.makedirs(profiles_dir, exist_ok=True)

    def save_profile(self, profile_name, config):
        """Save a profile configuration as JSON.

        Args:
            profile_name (str): Requested profile name.
            config (dict): Dashboard configuration to persist.

        Returns:
            str: Path to the saved profile file.
        """

        safe_name = "".join(c for c in profile_name if c.isalnum() or c in ("-", "_"))
        if not safe_name:
            safe_name = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = os.path.join(self.profiles_dir, f"{safe_name}.json")

        # Save the provided config as the profile JSON payload (flat config dict)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        return filepath

    def load_profile(self, profile_name):
        """Load a profile by sanitized name.

        Returns:
            dict | None: Profile configuration, or ``None`` when missing
            or unreadable.
        """

        safe_name = "".join(c for c in profile_name if c.isalnum() or c in ("-", "_"))
        filepath = os.path.join(self.profiles_dir, f"{safe_name}.json")

        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Profiles are stored as the raw config dict
            return data
        except Exception as e:
            print(f"Error loading profile: {e}")
            return None

    def list_profiles(self):
        """List saved profile names without the JSON extension."""

        profiles = []
        if os.path.exists(self.profiles_dir):
            for filename in os.listdir(self.profiles_dir):
                if filename.endswith(".json"):
                    profiles.append(filename[:-5])
        return sorted(profiles)

    def delete_profile(self, profile_name):
        """Delete a saved profile when it exists.

        Returns:
            bool: ``True`` when a profile file was removed.
        """

        safe_name = "".join(c for c in profile_name if c.isalnum() or c in ("-", "_"))
        filepath = os.path.join(self.profiles_dir, f"{safe_name}.json")

        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            print(f"Error deleting profile: {e}")

        return False
