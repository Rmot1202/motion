# Test Coverage Summary

This project includes focused automated tests for the parts that can break without a real MCC thermocouple board.

## Test files

### `tests/test_profiles.py`
- Verifies file-based profile management in isolation using `tmp_path`.
- Tests saving profiles with a safe filename.
- Tests loading saved profiles and validating returned config.
- Tests listing saved profiles.
- Tests deleting profiles.
- Tests missing profile handling returns `None`.
- Tests invalid JSON profile files are handled gracefully.
- Confirms profile storage is isolated to the temporary directory passed into `ProfileManager`.

### `tests/test_app_helpers.py`
- Tests dashboard helper logic that can run without Dash UI.
- Validates sampling frequency updates into an interval value.
- Validates `build_live_cfg()` resets invalid y-axis ranges and non-positive sampling values.
- Validates `make_figure()` uses store data and applies the configured y-axis range.
- Tests profile file loading returns defaults when the file is missing.
- Tests selected profile load returns the expected configuration values.
- Tests modal toggle helper logic using mocked callback context.

### `tests/test_hardware_wrapper.py`
- Tests the `MCCThermocouple` wrapper logic using mocked `mcculw`.
- Simulates missing MCC library behavior and fallback to simulation mode.
- Ensures connect succeeds when the fake library is available.
- Validates channel reads return mocked hardware values, including negative temperatures.
- Validates read failures fall back to simulated data without crashing.
- Validates `disconnect()` switches the wrapper into simulation mode cleanly.

### `tests/test_dash_callbacks.py`
- Tests button recording logic for start/stop flows.
- Verifies recording state updates, returned button states, and file naming.
- Verifies `update_temps()` writes recording data when recording is active.
- Verifies the simulation banner text and class appear when the hardware wrapper is in simulation mode.

## How to run tests

From the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pytest -q
```

Or run a single file:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_profiles.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_app_helpers.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_hardware_wrapper.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_dash_callbacks.py
```

## Notes

- These tests focus on file I/O, validation, helper functions, and callback logic.
- The hardware wrapper tests mock `mcculw` so the code path can be validated without the real device.
- The dashboard tests are limited to isolated logic and do not require a browser session.
