# MCCThermocouple

`MCCThermocouple` is a Python wrapper for an MCC E-TC Ethernet thermocouple device. It uses MCC's Universal Library through the `mcculw` Python package to read thermocouple temperatures in Celsius, while providing a simulation fallback when the hardware or library is unavailable.[1][2]

## Overview

The MCC E-TC is an Ethernet-based, 8-channel thermocouple measurement device designed for temperature acquisition over a network connection.[3][4] This class wraps the vendor library behind a simpler application-facing interface for connecting, reading channels, handling failures, and exposing device status.[1][5]

## Features

- Connect to an MCC E-TC device through the MCC Universal Library.[1][2]
- Read one or more thermocouple channels in Celsius using `TempScale.CELSIUS`.[2][5]
- Read all 8 channels with a helper method.[3][4]
- Fall back to simulation mode when the MCC library is missing or hardware reads fail.[2]
- Preserve partial-read behavior by returning `None` for failed channels while keeping successful channel values.[5]
- Expose device information for dashboards, diagnostics, or test utilities.[1][2]

## Requirements

- Windows system with MCC software installed, because the Python API is a wrapper over MCC's Universal Library for Windows.[1][2]
- MCC DAQ software and InstaCal installed and configured before use.[6]
- Python with the `mcculw` package available.[2][7]
- An MCC E-TC or compatible MCC temperature device configured in the MCC software environment.[6][3]

## Installation

1. Install MCC DAQ software and InstaCal.[6]
2. Install the Python package:

```bash
pip install mcculw
```

3. Configure the device in InstaCal or MCC software before running code that reads channels.[6]

## Example

```python
from hardware import MCCThermocouple

device = MCCThermocouple(device_ip="192.168.10.101", board_num=0)

if device.connect():
    temps = device.read_channels([0, 1, 2])
    print("Temperatures:", temps)
else:
    print("Using simulation mode")
```

## Class design

### Constructor

```python
MCCThermocouple(device_ip=None, device_id=None, board_num=0)
```

Arguments:

- `device_ip`: optional IP address for the MCC E-TC device.
- `device_id`: optional logical or inventory identifier.
- `board_num`: MCC board number used by the Universal Library.[1][2]

### Internal state

The class tracks connection state, simulation state, the most recent error, and a cached handle to the imported MCC Universal Library module.[2] It also suppresses repeated duplicate error logs through `_log_once`, which is useful when a dashboard polls the device repeatedly.

## Methods

### `connect()`

Attempts to initialize device access. If the `mcculw` library is unavailable, the object switches into simulation mode and returns `False`.[2] In the provided implementation, a successful connection assumes the MCC device has already been configured in InstaCal or MCC software rather than performing full device discovery inside the class.[6]

### `read_channels(channels=None)`

Reads one or more channels and returns a list of values. Thermocouple readings are requested in Celsius using the MCC Universal Library thermocouple input call path.[5][2]

Behavior:

- If hardware is unavailable, returns simulated values.
- If some channel reads fail, returns `None` for those channels and valid floats for the rest.
- If all channel reads fail, the class switches to simulation mode and returns simulated values.

### `read_single_channel(channel=0)`

Convenience wrapper around `read_channels()` for one channel.

### `read_all_channels()`

Returns values for channels `0` through `7`, matching the 8-channel nature of the MCC E-TC platform.[3][4]

### `disconnect()`

Marks the object as disconnected and enables simulation mode. This is a lightweight state transition in the current implementation rather than a full hardware teardown.

### `get_device_info()`

Returns a dictionary with device metadata and runtime state, including connection status, simulation status, board number, IP address, and maximum sampling-rate metadata.[3][4]

### `test_read()`

Runs a simple console-based connection and read test on channels `0`, `1`, and `2`, then prints either hardware data or a simulation notice.

## Simulation mode

Simulation mode is useful for UI development, testing, and offline debugging. If the MCC library cannot be imported or if all hardware channel reads fail, the class generates synthetic temperatures with small random noise rather than stopping the application.[2] This pattern is especially helpful for dashboards that need to remain usable even when the physical device is temporarily disconnected.

## Use cases

This class is a good fit for:

- Dash or Flask temperature-monitoring dashboards.
- Furnace or TUS logging tools.
- Lab data collection utilities.
- Development environments without live MCC hardware.
- Integration layers that need a consistent API for both real and simulated temperature data.

## Notes

The MCC E-TC product line is described as an Ethernet-based thermocouple measurement device with 8 channels and high-resolution temperature measurement capability.[3][4] MCC's Python package is not a standalone hardware driver; it is an interface to the vendor's Universal Library, so proper software installation and configuration remain part of deployment.[1][2][6]