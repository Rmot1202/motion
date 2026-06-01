# Thermocouple Dashboard

A Python **Dash web application** for monitoring MCC E-TC thermocouple channels, recording temperature data, and downloading files via HTTPS.

## Quick Start

### Local Development
```powershell
# Install dependencies
pip install -r requirements.txt

# Run the app
python appilcation/app.py
```
Open **http://localhost:8050/**

### Docker
```powershell
docker-compose up
```
Access via **https://localhost/** (self-signed certificate)

---

## Features

✅ **Live Temperature Monitoring**
- 3 channels: Outlet, Center, Inlet
- Real-time readings from MCC E-TC device (or simulator if offline)
- Color-coded display cards

✅ **Recording Management**
- Start/Stop buttons to record temperature data
- Files saved in LabVIEW-compatible TUS format
- Automatic timestamped filenames

✅ **File Downloads**
- Download recordings to your computer via button
- No server-side storage required for downloads

✅ **Configuration**
- Save furnace number, temperature setpoints, bounds
- Persistent settings (JSON-based)

✅ **Production Ready**
- NGINX reverse proxy with HTTPS
- Docker containerization
- Hardware fallback (simulated data when device offline)

---

## Project Structure

```
Thermocouple_dashboard/
├── appilcation/                    # Main application (note: typo is intentional)
│   ├── app.py                      # Dash frontend + callbacks
│   ├── config.py                   # Configuration constants
│   ├── hardware.py                 # MCC device interface
│   ├── profiles.py                 # Profile management
│   └── test_hardware.py
│
├── storage/                        # Docker volumes (not in git)
│   ├── recordings/                 # TUS temperature files
│   ├── profiles/                   # JSON configuration
│   └── logs/
│
├── docs/
│   ├── SIMPLIFIED_ARCHITECTURE.md  # System design
│   └── SETUP_GUIDE.md              # Installation guide
│
├── Dockerfile                      # Application container
├── docker-compose.yml              # Full stack (app + nginx)
├── requirements.txt                # Python dependencies
└── README.md
```

---

## Hardware Setup

**MCC E-TC Device**
- IP Address: `192.168.10.101`
- Channels: 8 (app uses 3: channels 0, 1, 2)
- Driver: `mcculw` v1.0.0

If the device is unavailable, the app runs in **simulator mode** with Gaussian noise.

---

## File Formats

### TUS Format (LabVIEW Compatible)
Temperature recording files in `/storage/recordings/`:
```
TUS_F{furnace}_{YYMMDD}_{HHMM}.txt
```
Tab-separated columns:
```
hour    minute  second  channel_0   channel_1   channel_2
```

Example:
```
14	23	45	75.123	76.456	74.890
14	23	46	75.145	76.478	74.912
```

### Configuration (JSON)
Saved to `/storage/profiles/` or `thermocouple_config.json/`:
```json
{
  "furnace_number": 1,
  "setpoint": 75.0,
  "lower_bound": 70.0,
  "upper_bound": 80.0
}
```

---

## Deployment

### Local with HTTPS
1. Generate SSL certificate:
   ```powershell
   openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
   ```

2. Update `docker-compose.yml` with certificate paths

3. Build and deploy:
   ```powershell
   docker-compose up -d
   ```

4. Access: **https://localhost/**

### Environment Variables
Create `.env` file:
```
MCC_DEVICE_IP=192.168.10.101
DASH_PORT=8050
POLLING_INTERVAL=1000
```

---

## Documentation

- [Simplified Architecture](docs/SIMPLIFIED_ARCHITECTURE.md) — System design and data flow
- [Setup Guide](docs/SETUP_GUIDE.md) — Installation and configuration
- [MCC Hardware](MCC_HARDWARE_GUIDE.md) — Device specifications

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Device offline | App switches to simulator mode automatically |
| Temperature readings stuck | Check device IP (192.168.10.101) and network connectivity |
| Files not downloading | Ensure `/storage/recordings/` volume is mounted in Docker |
| HTTPS certificate warning | Use self-signed cert (expected for local development) |

---

## Development

### Install for development
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Run tests
```powershell
python appilcation/test_hardware.py
```

### Modify app
Edit `appilcation/app.py` and refresh browser (hot reload enabled)

---

## License & Support

Built with [Dash](https://dash.plotly.com/) | Controlled by MCC E-TC Library
