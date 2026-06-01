# Simplified Thermocouple Dashboard - Architecture

**Version**: 2.0 (Dash-Based)  
**Status**: Production-Ready  
**Framework**: Python Dash + Bootstrap Components

---

## System Architecture

```
┌─────────────────────────────────────────────┐
│           User's Web Browser                │
│  (Chrome, Firefox, Safari, Edge)            │
└────────────────┬────────────────────────────┘
                 │ HTTPS (port 443)
                 ↓
┌─────────────────────────────────────────────┐
│         NGINX Reverse Proxy                 │
│  - SSL/TLS termination                      │
│  - Proxies requests to Dash app             │
│  - Port 443 → app:8050                      │
└────────────────┬────────────────────────────┘
                 │ HTTP (internal)
                 ↓
┌─────────────────────────────────────────────┐
│    Python Dash Application (appilcation/)   │
│  ┌─────────────────────────────────────┐    │
│  │ app.py - Main Application           │    │
│  │  • Bootstrap UI components          │    │
│  │  • Real-time callbacks              │    │
│  │  • File downloads                   │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │ hardware.py - Device Interface      │    │
│  │  • MCCThermocouple class            │    │
│  │  • Reads 3 channels                 │    │
│  │  • Fallback simulator               │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │ config.py - Settings                │    │
│  │ profiles.py - Config Management     │    │
│  └─────────────────────────────────────┘    │
└────────────────┬────────────────────────────┘
                 │ TCP/IP
                 ↓
┌─────────────────────────────────────────────┐
│   MCC E-TC Hardware Device                  │
│   IP: 192.168.10.101                        │
│   8 Thermocouple Channels                   │
│   (App uses 0, 1, 2)                        │
└─────────────────────────────────────────────┘
```

---

## Project Structure

```
Thermocouple_dashboard/
│
├── appilcation/                     # Main Python application
│   ├── app.py                       # Dash frontend + callbacks
│   ├── config.py                    # Constants & settings
│   ├── hardware.py                  # MCC device interface
│   ├── profiles.py                  # JSON profile management
│   └── test_hardware.py             # Hardware tests
│
├── storage/                         # Docker volumes (not in git)
│   ├── recordings/                  # TUS temperature files
│   ├── profiles/                    # JSON configurations
│   └── logs/                        # Application logs
│
├── docs/
│   ├── SIMPLIFIED_ARCHITECTURE.md   # (this file)
│   └── SETUP_GUIDE.md               # Installation guide
│
├── nginx/                           # (future) NGINX configs
│
├── ssl/                             # (future) SSL certificates
│   ├── cert.pem
│   └── key.pem
│
├── Dockerfile                       # App container definition
├── docker-compose.yml               # Multi-container orchestration
├── requirements.txt                 # Python dependencies
└── README.md
```

---

## Component Breakdown

### 1. Frontend (Dash + Bootstrap Components)

**File**: `appilcation/app.py`

```python
# Dash provides:
- HTTP server (no separate web framework needed)
- Real-time callbacks (no WebSocket complexity)
- File downloads (built-in dcc.Download)
- Bootstrap responsive UI (via dash_bootstrap_components)
```

**Features**:
- Temperature display cards (3 channels, color-coded)
- Recording start/stop buttons
- Configuration panel (furnace #, setpoint, bounds)
- Download button (latest TUS file)
- Real-time polling (every 1 second)

### 2. Backend (Python Hardware Interface)

**File**: `appilcation/hardware.py`

```python
class MCCThermocouple:
    - connect()           # Connect to device
    - read_channels()     # Get 3 temp readings
    - simulator mode      # Fallback if offline
```

**Features**:
- Reads from MCC E-TC device via TCP/IP (192.168.10.101)
- Returns Celsius values (3 decimal places)
- Automatic fallback to simulated data
- No external API complexity

### 3. Data Management

**Recording** (`profiles.py`):
- Start/Stop buttons save TUS files
- Filename: `TUS_F{furnace}_{YYMMDD}_{HHMM}.txt`
- Tab-separated: `hour minute second ch0 ch1 ch2`
- Stored in `/storage/recordings/`

**Configuration** (`config.py`):
- Furnace number
- Setpoint, lower bound, upper bound
- Saved as JSON in `thermocouple_config.json/`
- Persisted across restarts

### 4. NGINX Reverse Proxy

**Role**:
- Terminates HTTPS/SSL (port 443 → app:8050)
- Routes traffic to Dash app
- Serves static files (optional)
- Handles compression, caching

**Not needed locally** (Flask/Dash handles HTTP directly)  
**Needed for production** (HTTPS requirement)

---

## Data Flow

### Temperature Polling Loop

```
┌─────────────────────────────────────────────┐
│ User Opens Browser Tab                      │
│ → Dash app.py serves HTML/JS                │
│ → Browser renders UI                        │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│ Callback: update_temps()                    │
│ Triggered every 1000ms by dcc.Interval      │
│                                             │
│ 1. hardware.read_channels() → [72.5, ...]   │
│ 2. Format for display: "72.5 °C"            │
│ 3. Update HTML cards on page                │
│ 4. If recording: write row to TUS file      │
└──────────────┬──────────────────────────────┘
               │
               ↓ (Repeats every second)
           ∞ Loop
```

### Recording Start/Stop

```
User clicks "Start Recording"
    ↓
Callback: handle_recording()
    ↓
Create file: /storage/recordings/TUS_F1_260601_1430.txt
    ↓
Set recording_state['active'] = True
    ↓
update_temps() now appends rows
    ↓
User clicks "Stop Recording"
    ↓
Set recording_state['active'] = False
    ↓
File closed automatically (context manager)
```

### File Download

```
User clicks "Download"
    ↓
Callback: download_latest()
    ↓
Find latest file in /storage/recordings/
    ↓
Browser receives dcc.send_file()
    ↓
Browser shows "Save As" dialog
    ↓
User's computer: ~/Downloads/TUS_F1_260601_1430.txt
```

---

## Key Design Decisions

| Decision | Why |
|----------|-----|
| **Dash instead of FastAPI** | Integrated UI + callbacks, no API layer needed |
| **Callbacks instead of WebSockets** | Simpler, built-in refresh mechanism, no connection state |
| **TUS file format** | LabVIEW compatible, meets legacy requirements |
| **JSON config** | Human-readable, easy version control later |
| **Simulator fallback** | Graceful degradation when hardware unavailable |
| **Bootstrap CSS** | Professional look, responsive, minimal custom styling |
| **Docker + NGINX** | Production-ready HTTPS without code changes |

---

## Deployment Scenarios

### Development (Local)
```
1. pip install -r requirements.txt
2. python appilcation/app.py
3. Open http://localhost:8050/
```

### Testing (Docker)
```
1. docker-compose up --build
2. Access http://localhost:8050/
```

### Production (HTTPS)
```
1. Generate SSL certificates (ssl/cert.pem, ssl/key.pem)
2. docker-compose -f docker-compose.yml up -d
3. Access https://thermocouple.local/ (or FQDN)
```

---

## Dependencies

**Runtime**:
- `dash` - Web framework & UI components
- `dash-bootstrap-components` - Responsive styling
- `mcculw` - MCC device driver
- `plotly` - (optional, for future graphing)

**Development**:
- `pytest` - Testing framework
- `black` - Code formatter

See `requirements.txt` for pinned versions.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| MCC device offline | Automatically switches to simulator, shows in UI |
| Bad configuration | Loads defaults, continues |
| Disk full (recordings) | Recording stops, user notified |
| Network disconnect | Polling continues, UI updates on reconnect |

---

## Future Enhancements

- [ ] Historical data graphing (Plotly)
- [ ] Email/Slack notifications on temperature alert
- [ ] Multi-furnace support
- [ ] Data export (CSV, Excel)
- [ ] Mobile-responsive improvements
- [ ] API for external integrations (if needed)

---

## Security Notes

**Current Status**: Suitable for **lab use only**

- ✅ HTTPS ready (via NGINX)
- ✅ Docker isolation
- ⚠️ No authentication (add if exposed to internet)
- ⚠️ No input validation (assumes trusted local users)
- ✅ No sensitive data stored locally

**For internet exposure**, add:
1. Basic authentication (NGINX or Flask-Login)
2. Rate limiting
3. CORS restrictions
4. API key validation

---

## Support & Troubleshooting

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for common issues.

**Test hardware connection**:
```powershell
python appilcation/test_hardware.py
```

**Check logs** (Docker):
```powershell
docker logs thermocouple-dashboard
```

**Reset configuration**:
```powershell
rm thermocouple_config.json/config.json
# Then restart app
```

