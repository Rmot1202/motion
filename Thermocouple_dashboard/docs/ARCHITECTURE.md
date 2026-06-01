# Architecture

## Runtime Flow

```text
Dash UI
  -> dcc.Interval polling
  -> read_thermocouple_data()
  -> MCCThermocouple.read_channels([0, 1, 2])
  -> rolling in-browser data store
  -> graph/value-card updates
  -> optional TUS text append while recording
```

The application source lives under `appilcation/`. The project root intentionally has no Python source files.

## Modules

- `appilcation/app.py`: Dash layout, callbacks, config load/save, TUS filename and row formatting
- `appilcation/config.py`: defaults, channel count, colors, polling interval, output directory
- `appilcation/hardware.py`: MCC E-TC connection and simulated-data fallback
- `appilcation/profiles.py`: profile JSON save/load/list/delete helpers
- `appilcation/test_hardware.py`: command-line hardware test

## Key Callbacks

- `update_graph_and_values()`: polls temperatures, keeps a 5-minute rolling window, updates real-time graph traces, and updates current-value displays
- `update_config()`: persists UI setting changes
- `handle_recording()`: creates the active `TUS_F#_YYMMDD_HHMM.txt` file and toggles recording state
- `write_tus_file()`: appends the latest data row while recording is enabled
- `save_current_profile()`: writes the current config into `profiles/`

## TUS Recording Format

Files are named:

```text
TUS_F< furnace >_<YYMMDD>_<HHMM>.txt
```

Rows are tab-separated, headerless, and formatted to three decimals:

```text
hour	minute	second	channel_0	channel_1	channel_2
```

Example:

```text
14.000	7.000	37.010	812.500	890.200	910.000
```

## Persistence

- Recordings: `recordings/`
- Profiles: `profiles/`
- Config: `thermocouple_config.json/config.json` when `thermocouple_config.json` exists as a directory; otherwise `thermocouple_config.json`

## Docker

The image copies `appilcation/` into `/app/appilcation/` and starts:

```text
python -m appilcation.app
```

The app writes recordings and profiles under `/app/recordings` and `/app/profiles`, which are mounted by `docker-compose.yml`.
