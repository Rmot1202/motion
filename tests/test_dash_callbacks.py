"""Regression tests for Dash callbacks with file-writing side effects."""

import json
import types
from pathlib import Path

from appilcation import app as dash_app


def test_handle_recording_start_and_stop(monkeypatch, tmp_path):
    """Recording controls should create and then stop a TUS log."""

    monkeypatch.setattr(dash_app, "ctx", types.SimpleNamespace(triggered_id="btn-start"))
    rec_data = {"active": False, "filename": None}

    btn_start_disabled, btn_stop_disabled, rec_status, rec_file, updated_rec_data = dash_app.handle_recording(
        start_n=1,
        stop_n=0,
        furnace=2,
        rec_data=rec_data,
    )

    assert btn_start_disabled is True
    assert btn_stop_disabled is False
    assert rec_status == "Status: Recording"
    assert rec_file.startswith("File: TUS_F2_")
    assert updated_rec_data["active"] is True
    assert updated_rec_data["filename"].startswith("TUS_F2_")

    monkeypatch.setattr(dash_app, "ctx", types.SimpleNamespace(triggered_id="btn-stop"))
    btn_start_disabled, btn_stop_disabled, rec_status, rec_file, stopped_rec_data = dash_app.handle_recording(
        start_n=0,
        stop_n=1,
        furnace=2,
        rec_data=updated_rec_data,
    )

    assert btn_start_disabled is False
    assert btn_stop_disabled is True
    assert rec_status == "Status: Idle"
    assert rec_file.startswith("Saved: TUS_F2_")
    assert stopped_rec_data["active"] is False
    assert stopped_rec_data["filename"] == updated_rec_data["filename"]


def test_update_temps_writes_recording_and_simulation_banner(monkeypatch, tmp_path):
    """Temperature updates should record rows and show simulation state."""

    temp_data = [12.3, 13.4, 14.5]
    monkeypatch.setattr(dash_app, "read_live_temps", lambda: temp_data)
    monkeypatch.setattr(dash_app, "RECORDINGS_DIR", tmp_path)
    dash_app.hardware.simulation_mode = True

    existing_store = {"times": [], "ch0": [], "ch1": [], "ch2": []}
    record_state = {"active": True, "filename": "live_test.txt"}

    outputs = dash_app.update_temps(
        1,
        furnace=3,
        setpoint=80,
        lower=75,
        upper=85,
        y_min=50,
        y_max=100,
        sampling=1.0,
        store=existing_store,
        rec_data=record_state,
    )

    temp0, temp1, temp2, fig, new_store, status_text, status_class, machine_label, now, device_info, banner_text, banner_class, rec_status, rec_file, updated_rec_data = outputs

    assert temp0 != "--"
    assert temp1 != "--"
    assert temp2 != "--"
    assert rec_status == "Status: Recording"
    assert rec_file == "File: live_test.txt"
    assert banner_text == "Simulation mode — live MCC hardware not detected"
    assert banner_class == "data-mode-banner data-mode-sim"
    assert updated_rec_data["active"] is True
    assert updated_rec_data["filename"] == "live_test.txt"
    assert (tmp_path / "live_test.txt").exists()

    recorded_text = (tmp_path / "live_test.txt").read_text(encoding="utf-8")
    assert "# TUS Recording" in recorded_text or "12.300" in recorded_text
