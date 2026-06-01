# MCC E-TC Hardware Guide

## Requirements

- MCC E-TC device connected over Ethernet
- MCC drivers/device manager installed on the host
- Python package from `requirements.txt`, including `mcculw`

## Configure Device IP

Set the device IP in `appilcation/config.py`:

```python
DEVICE_IP = "192.168.1.100"
```

Leave it as `None` to auto-discover or use simulated data when hardware is unavailable.

## Test Hardware

Run:

```powershell
python appilcation/test_hardware.py
```

Optional arguments:

```powershell
python appilcation/test_hardware.py 192.168.1.100
python appilcation/test_hardware.py 192.168.1.100 1
```

The app reads channels `0`, `1`, and `2`.

## Dashboard Startup

Local:

```powershell
python appilcation/app.py
```

Docker:

```powershell
docker compose up --build
```

## Fallback Behavior

If the MCC library or hardware connection is unavailable, the dashboard logs a warning and uses simulated values. This keeps the UI and recording workflow testable without the physical device.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No MCC devices found | Device power, Ethernet connection, MCC driver install |
| Wrong readings | Thermocouple wiring and channel assignment |
| Cannot connect by IP | `DEVICE_IP`, firewall, network route |
| Docker has simulated data | Container may not have host MCC driver/device access |

## References

- MCC Python library: `mcculw`
- MCC E-TC user guide and MCC software documentation
