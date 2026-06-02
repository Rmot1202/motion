import json
from pathlib import Path

from appilcation.profiles import ProfileManager


def test_save_and_load_profile(tmp_path):
    profiles_dir = tmp_path / "profiles"
    manager = ProfileManager(str(profiles_dir))

    config = {"furnace_number": 3, "setpoint": 95.7, "y_min": -20.0, "y_max": 110.0}
    filepath = manager.save_profile("cool_profile", config)
    filepath = Path(filepath)

    assert filepath.parent == profiles_dir
    assert (profiles_dir / "cool_profile.json").exists()

    loaded = manager.load_profile("cool_profile")
    assert loaded == config


def test_list_and_delete_profiles(tmp_path):
    manager = ProfileManager(str(tmp_path))
    manager.save_profile("first", {"furnace_number": 1})
    manager.save_profile("second_profile", {"furnace_number": 2})

    assert manager.list_profiles() == ["first", "second_profile"]

    assert manager.delete_profile("first") is True
    assert manager.list_profiles() == ["second_profile"]


def test_load_missing_profile_returns_none(tmp_path):
    manager = ProfileManager(str(tmp_path))
    assert manager.load_profile("does_not_exist") is None


def test_load_invalid_profile_returns_none(tmp_path):
    manager = ProfileManager(str(tmp_path))
    invalid_path = tmp_path / "broken.json"
    invalid_path.write_text("{ not valid json }", encoding="utf-8")

    assert manager.load_profile("broken") is None


def test_profile_name_sanitization_uses_safe_filename(tmp_path):
    manager = ProfileManager(str(tmp_path))
    filepath = manager.save_profile("Profile!@#$%^&*() Name", {"furnace_number": 5})

    assert filepath.endswith("ProfileName.json")
    assert (tmp_path / "ProfileName.json").exists()
