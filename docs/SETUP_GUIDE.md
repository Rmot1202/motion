# Setup Guide

Quick installation and configuration guide for the Thermocouple Dashboard.

---

## Prerequisites

- Python 3.8+ (or use Docker)
- MCC E-TC device (optional; simulator available)
- Git
- Docker & Docker Compose (optional, for containerized deployment)

---

## Local Installation

### 1. Clone and Install Dependencies

```powershell
cd c:\path\to\Thermocouple_dashboard
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Hardware (Optional)

Edit `appilcation/config.py`:

```python
DEVICE_IP = "192.168.10.101"  # Change if using different device
DEFAULT_FURNACE_NUMBER = 1
POLLING_INTERVAL = 1000       # milliseconds
```

### 3. Run the Application

```powershell
python appilcation/app.py
```

Open your browser to **http://localhost:8050/**

---

## Docker Setup

### 1. Build Container

```powershell
docker-compose build
```

### 2. Create Storage Directories (if not using Docker volumes)

```powershell
mkdir storage/recordings
mkdir storage/profiles
mkdir storage/logs
```

### 3. Run Container

```powershell
docker-compose up
```

Access at **http://localhost:8050/**

---

## HTTPS Deployment (Production)

### 1. Generate Self-Signed Certificate

```powershell
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"
```

Save to `./ssl/` directory.

### 2. Update docker-compose.yml

Ensure volumes are mounted:

```yaml
volumes:
  - ./ssl/cert.pem:/etc/nginx/ssl/cert.pem:ro
  - ./ssl/key.pem:/etc/nginx/ssl/key.pem:ro
```

### 3. Deploy

```powershell
docker-compose up -d
```

Access at **https://localhost/** (accept the self-signed certificate warning)

---

## Configuration

### Application Settings

Navigate to the "Configuration" panel in the web interface:

- **Furnace Number**: Used in recorded filename (`TUS_F{N}_...`)
- **Setpoint (°C)**: Target temperature
- **Lower Bound (°C)**: Alarm threshold (low)
- **Upper Bound (°C)**: Alarm threshold (high)

Settings are saved automatically to `thermocouple_config.json/config.json`.

### Environment Variables

Create `.env` file in project root:

```env
# Device Configuration
MCC_DEVICE_IP=192.168.10.101

# Application
DASH_PORT=8050
POLLING_INTERVAL=1000

# Storage (Docker)
STORAGE_PATH=/storage
```

---

## Data Storage

### Recordings

Temperature data is stored as TUS (LabVIEW-compatible) text files:

**Location**: `/storage/recordings/` (or `./recordings/` locally)

**Filename Format**: `TUS_F{furnace}_{YYMMDD}_{HHMM}.txt`

**Example Content**:
```
14	23	45	75.123	76.456	74.890
14	23	46	75.145	76.478	74.912
```

### Configuration

Profiles are stored as JSON:

**Location**: `/storage/profiles/` or `thermocouple_config.json/`

**Example**:
```json
{
  "furnace_number": 1,
  "setpoint": 75.0,
  "lower_bound": 70.0,
  "upper_bound": 80.0
}
```

---

## Hardware Testing

### Test MCC Device Connection

```powershell
python appilcation/test_hardware.py
```

Expected output if connected:
```
✓ MCC device connected at 192.168.10.101
✓ Channels 0, 1, 2 available
```

If offline, you'll see:
```
⚠ Device offline, using simulator
```

### Simulator Mode

If the MCC device is unavailable, the app automatically uses simulated data with Gaussian noise (N(0, 0.5°C)).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Port 8050 already in use** | Change port in `docker-compose.yml` or `appilcation/app.py` |
| **Device not found** | Verify IP address in `config.py` and network connectivity |
| **Temperature readings freeze** | Check device connectivity; app will switch to simulator |
| **Docker volume permission error** | Run `docker-compose up --user root` or fix ownership |
| **HTTPS certificate warning** | Normal for self-signed certs; click "Accept" in browser |
| **Recording file empty** | Ensure at least 1 polling interval passes before stopping |

---

## Next Steps

1. ✅ **Verify Hardware**: Run `test_hardware.py` to confirm MCC device connectivity
2. 🎯 **Start Recording**: Use the web interface to begin monitoring
3. 📊 **Download Data**: Use the download button to retrieve TUS files
4. 🔒 **Deploy**: Configure HTTPS and deploy with Docker

---

## Support

- See [MCC_HARDWARE_GUIDE.md](../MCC_HARDWARE_GUIDE.md) for device specifications
- See [SIMPLIFIED_ARCHITECTURE.md](SIMPLIFIED_ARCHITECTURE.md) for system design
