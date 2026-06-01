"""
Thermocouple Dashboard - Simplified Dash Application

A lightweight Dash app that monitors MCC E-TC Ethernet thermocouple device
with real-time temperature display, recording, and file downloads.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

try:
    from . import config
    from .hardware import MCCThermocouple
    from .profiles import ProfileManager
except ImportError:
    import config
    from hardware import MCCThermocouple
    from profiles import ProfileManager

# ========================================
# Configuration
# ========================================

STORAGE_PATH = Path(os.getenv('STORAGE_PATH', './storage'))
RECORDINGS_DIR = STORAGE_PATH / 'recordings'
PROFILES_DIR = STORAGE_PATH / 'profiles'
CONFIG_FILE = PROFILES_DIR / 'current_config.json'

# Create directories
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

DEVICE_IP = config.DEVICE_IP
POLLING_INTERVAL = config.POLLING_INTERVAL

# ========================================
# Initialize
# ========================================

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Thermocouple Dashboard"

profile_manager = ProfileManager()
hardware = MCCThermocouple(device_ip=DEVICE_IP)

# ========================================
# Configuration Management
# ========================================

DEFAULT_CONFIG = {
    "furnace_number": config.DEFAULT_FURNACE_NUMBER,
    "setpoint": config.DEFAULT_SETPOINT,
    "lower_bound": config.DEFAULT_LOWER_BOUND,
    "upper_bound": config.DEFAULT_UPPER_BOUND,
}


def load_config():
    """Load configuration from JSON"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG.copy()


def save_config(cfg):
    """Save configuration to JSON"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)


# ========================================
# Layout
# ========================================

current_config = load_config()

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("🌡️ Thermocouple Monitor", className="text-center mb-2 mt-4"),
            html.P(
                id="status-indicator",
                className="text-center lead",
                children="✓ Connected"
            )
        ])
    ], className="mb-4"),
    
    # Data storage
    dcc.Store(id='data-store', data={'times': [], 'ch0': [], 'ch1': [], 'ch2': []}),
    dcc.Store(id='config-store', data=current_config),
    dcc.Store(id='recording-store', data={'active': False, 'filename': None}),
    
    # Polling interval
    dcc.Interval(id='interval', interval=POLLING_INTERVAL, n_intervals=0),
    
    # Temperature Display Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Outlet (Channel 0)"),
                    html.H2(id="temp-0", children="--", className="text-primary"),
                    html.Small("°C", className="text-muted")
                ], className="text-center")
            ], className="mb-3")
        ], md=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Center (Channel 1)"),
                    html.H2(id="temp-1", children="--", className="text-success"),
                    html.Small("°C", className="text-muted")
                ], className="text-center")
            ], className="mb-3")
        ], md=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Inlet (Channel 2)"),
                    html.H2(id="temp-2", children="--", className="text-danger"),
                    html.Small("°C", className="text-muted")
                ], className="text-center")
            ], className="mb-3")
        ], md=4),
    ], className="mb-4"),
    
    # Recording Controls
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Recording")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "▶ Start",
                                id="btn-start",
                                color="success",
                                className="w-100"
                            )
                        ], md=6),
                        dbc.Col([
                            dbc.Button(
                                "⏹ Stop",
                                id="btn-stop",
                                color="danger",
                                disabled=True,
                                className="w-100"
                            )
                        ], md=6),
                    ]),
                    html.Hr(),
                    html.Div(id="rec-status", children="Status: Idle"),
                    html.Small(id="rec-file", className="text-muted d-block mt-2")
                ])
            ])
        ], md=6),
        
        # Download
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Download")),
                dbc.CardBody([
                    html.P("Save recording to your computer:"),
                    dbc.Button(
                        "📥 Download",
                        id="btn-download",
                        color="info",
                        disabled=True,
                        className="w-100"
                    ),
                    dcc.Download(id="download-file"),
                    html.Div(id="download-status", className="mt-2")
                ])
            ])
        ], md=6)
    ], className="mb-4"),
    
    # Configuration
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Configuration")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Furnace Number"),
                            dbc.Input(
                                id="cfg-furnace",
                                type="number",
                                value=current_config.get('furnace_number', 1),
                                min=1
                            )
                        ], md=6),
                        dbc.Col([
                            dbc.Label("Setpoint (°C)"),
                            dbc.Input(
                                id="cfg-setpoint",
                                type="number",
                                value=current_config.get('setpoint', 75.0),
                                step=0.1
                            )
                        ], md=6),
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Lower Bound (°C)"),
                            dbc.Input(
                                id="cfg-lower",
                                type="number",
                                value=current_config.get('lower_bound', 70.0),
                                step=0.1
                            )
                        ], md=6),
                        dbc.Col([
                            dbc.Label("Upper Bound (°C)"),
                            dbc.Input(
                                id="cfg-upper",
                                type="number",
                                value=current_config.get('upper_bound', 80.0),
                                step=0.1
                            )
                        ], md=6),
                    ]),
                    dbc.Button(
                        "💾 Save",
                        id="btn-save-cfg",
                        color="primary",
                        className="w-100 mt-3"
                    )
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Footer
    html.Hr(),
    html.Footer(
        html.P("Thermocouple Dashboard v2.0 • Simplified Edition", className="text-center text-muted"),
        className="mb-4"
    )

], fluid=True, style={'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 'minHeight': '100vh'})

# ========================================
# Callbacks
# ========================================

@callback(
    [
        Output('temp-0', 'children'),
        Output('temp-1', 'children'),
        Output('temp-2', 'children'),
        Output('data-store', 'data'),
    ],
    Input('interval', 'n_intervals')
)
def update_temps(n):
    """Update temperature display every second"""
    temps = hardware.read_channels([0, 1, 2])
    if temps is None:
        temps = [0, 0, 0]
    
    # Record if active
    store = {
        'times': [],
        'ch0': [],
        'ch1': [],
        'ch2': []
    }
    
    return (
        f"{temps[0]:.1f}",
        f"{temps[1]:.1f}",
        f"{temps[2]:.1f}",
        store
    )

@callback(
    [
        Output('btn-start', 'disabled'),
        Output('btn-stop', 'disabled'),
        Output('rec-status', 'children'),
        Output('rec-file', 'children'),
        Output('btn-download', 'disabled'),
        Output('recording-store', 'data'),
    ],
    [
        Input('btn-start', 'n_clicks'),
        Input('btn-stop', 'n_clicks'),
    ],
    [State('cfg-furnace', 'value'), State('recording-store', 'data')],
    prevent_initial_call=True
)
def handle_recording(start_n, stop_n, furnace, rec_data):
    """Handle recording start/stop"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        raise PreventUpdate
    
    button = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button == 'btn-start':
        # Start recording
        timestamp = datetime.now().strftime('%y%m%d_%H%M')
        filename = f'TUS_F{int(furnace or 1)}_{timestamp}.txt'
        filepath = RECORDINGS_DIR / filename
        
        # Create empty file
        with open(filepath, 'w') as f:
            f.write(f"# Recording started {datetime.now().isoformat()}\n")
        
        rec_data['active'] = True
        rec_data['filename'] = filename
        
        return False, True, "Status: ⏹ Recording", f"File: {filename}", True, rec_data
    
    elif button == 'btn-stop':
        # Stop recording
        rec_data['active'] = False
        filename = rec_data.get('filename', 'unknown')
        
        return True, False, "Status: Idle", f"Saved: {filename}", False, rec_data
    
    raise PreventUpdate

@callback(
    Output('download-file', 'data'),
    Input('btn-download', 'n_clicks'),
    prevent_initial_call=True
)
def download_latest(n):
    """Download latest recording file"""
    files = sorted(RECORDINGS_DIR.glob('TUS_*.txt'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if files:
        return dcc.send_file(str(files[0]), as_attachment=True)
    
    raise PreventUpdate

@callback(
    Output('config-store', 'data'),
    Input('btn-save-cfg', 'n_clicks'),
    [
        State('cfg-furnace', 'value'),
        State('cfg-setpoint', 'value'),
        State('cfg-lower', 'value'),
        State('cfg-upper', 'value'),
    ],
    prevent_initial_call=True
)
def save_config_callback(n, furnace, setpoint, lower, upper):
    """Save configuration"""
    cfg = {
        'furnace_number': int(furnace or 1),
        'setpoint': float(setpoint or 75.0),
        'lower_bound': float(lower or 70.0),
        'upper_bound': float(upper or 80.0),
    }
    
    save_config(cfg)
    return cfg

# ========================================
# Run
# ========================================

if __name__ == '__main__':
    if not hardware.connected:
        hardware.connect()
        if not hardware.connected:
            print("⚠️  Warning: Could not connect to hardware. Using simulated data.")
    
    print("🚀 Starting Thermocouple Dashboard at http://0.0.0.0:8050/")
    app.run_server(debug=False, host='0.0.0.0', port=8050)
