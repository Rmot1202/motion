"""Run the Dash thermocouple dashboard.

The module builds the dashboard layout, manages furnace configuration
profiles, reads MCC E-TC thermocouple values, and records TUS-compatible
temperature logs.
"""

import os
import json
from datetime import datetime
from pathlib import Path

import dash
from dash import dcc, html, Input, Output, State, clientside_callback, ctx
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

try:
    from . import config
    from .hardware import MCCThermocouple
    from .profiles import ProfileManager
except ImportError:
    import config
    from hardware import MCCThermocouple
    from profiles import ProfileManager


STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "./storage"))
RECORDINGS_DIR = STORAGE_PATH / "recordings"
PROFILES_DIR = STORAGE_PATH / "profiles"
CONFIG_FILE = PROFILES_DIR / "current_config.json"

RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

DEVICE_IP = config.DEVICE_IP
GRAPH_WINDOW_SECONDS = getattr(config, "GRAPH_WINDOW_SECONDS", 300)
GRAPH_HEIGHT = getattr(config, "GRAPH_HEIGHT", 400)
BASE_PATH = os.getenv("DASH_BASE_PATHNAME", "/")

DEFAULT_CONFIG = {
    "furnace_number": getattr(config, "DEFAULT_FURNACE_NUMBER", 1),
    "setpoint": getattr(config, "DEFAULT_SETPOINT", 75.0),
    "lower_bound": getattr(config, "DEFAULT_LOWER_BOUND", 70.0),
    "upper_bound": getattr(config, "DEFAULT_UPPER_BOUND", 80.0),
    "y_min": getattr(config, "DEFAULT_Y_MIN", 60.0),
    "y_max": getattr(config, "DEFAULT_Y_MAX", 90.0),
    "sampling_frequency": float(getattr(config, "DEFAULT_SAMPLING_FREQUENCY", 1.0)),
}

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    url_base_pathname=BASE_PATH,
)
app.title = "Thermocouple Dashboard"

profile_manager = ProfileManager(str(PROFILES_DIR))
hardware = MCCThermocouple(device_ip=DEVICE_IP)


def load_config():
    """Load the persisted dashboard configuration.

    Returns:
        dict: The saved configuration merged over the application defaults.
    """

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        merged = DEFAULT_CONFIG.copy()
        merged.update(loaded)
        return merged
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(cfg):
    """Persist the active dashboard configuration.

    Args:
        cfg (dict): Configuration values to write as JSON.
    """

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def list_profile_options():
    """Build Dash dropdown options for saved furnace profiles.

    Returns:
        list[dict]: Options with display labels and profile filenames.
    """

    options = []
    for path in sorted(PROFILES_DIR.glob("*.json")):
        if path.name == CONFIG_FILE.name:
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            furnace = cfg.get("furnace_number")
            if furnace is None:
                continue
            options.append({"label": f"Furnace {int(furnace)}", "value": path.name})
        except Exception:
            continue
    return options


def load_profile_file(filename):
    """Load a furnace profile by filename.

    Args:
        filename (str): JSON profile filename under ``PROFILES_DIR``.

    Returns:
        dict: Profile values merged over the application defaults.
    """

    path = PROFILES_DIR / filename
    if not path.exists():
        return DEFAULT_CONFIG.copy()
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    merged = DEFAULT_CONFIG.copy()
    merged.update(loaded)
    return merged


def fmt_temp(value):
    """Format a temperature value for display."""

    return f"{value:.3f}" if isinstance(value, (int, float)) else "--"


def simulate_values(count=3):
    """Generate fallback thermocouple values when hardware is unavailable.

    Args:
        count (int, optional): Number of channels to simulate.

    Returns:
        list[float]: Simulated channel temperatures.
    """

    try:
        return hardware._simulate(count)
    except Exception:
        import random
        return [72.0 + random.uniform(-1.0, 1.0) + i * 2 for i in range(count)]


def read_live_temps():
    """Read three thermocouple channels with simulation fallback.

    Returns:
        list[float | None]: Channel 1 through 3 temperatures.
    """

    temps = hardware.read_channels([0, 1, 2]) if hardware.connected else simulate_values(3)
    if temps is None:
        temps = simulate_values(3)
    return [
        temps[0] if len(temps) > 0 and temps[0] is not None else None,
        temps[1] if len(temps) > 1 and temps[1] is not None else None,
        temps[2] if len(temps) > 2 and temps[2] is not None else None,
    ]


def build_live_cfg(furnace, setpoint, lower, upper, y_min, y_max, sampling):
    """Normalize live form values into a dashboard configuration.

    Invalid sampling values and inverted y-axis bounds are reset to the
    configured defaults.
    """

    cfg = {
        "furnace_number": int(furnace) if furnace is not None else DEFAULT_CONFIG["furnace_number"],
        "setpoint": float(setpoint) if setpoint is not None else DEFAULT_CONFIG["setpoint"],
        "lower_bound": float(lower) if lower is not None else DEFAULT_CONFIG["lower_bound"],
        "upper_bound": float(upper) if upper is not None else DEFAULT_CONFIG["upper_bound"],
        "y_min": float(y_min) if y_min is not None else DEFAULT_CONFIG["y_min"],
        "y_max": float(y_max) if y_max is not None else DEFAULT_CONFIG["y_max"],
        "sampling_frequency": float(sampling) if sampling is not None else DEFAULT_CONFIG["sampling_frequency"],
    }

    if cfg["sampling_frequency"] <= 0:
        cfg["sampling_frequency"] = DEFAULT_CONFIG["sampling_frequency"]

    if cfg["y_min"] >= cfg["y_max"]:
        cfg["y_min"] = DEFAULT_CONFIG["y_min"]
        cfg["y_max"] = DEFAULT_CONFIG["y_max"]

    return cfg


def make_figure(store, cfg):
    """Create the live temperature chart.

    Args:
        store (dict): Time-series values stored by Dash.
        cfg (dict): Active furnace and graph configuration.

    Returns:
        plotly.graph_objects.Figure: Configured temperature chart.
    """

    times = store.get("times", [])
    ch0 = store.get("ch0", [])
    ch1 = store.get("ch1", [])
    ch2 = store.get("ch2", [])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=ch0, mode="lines", name="Channel 1", line=dict(color="#3b82f6", width=2)))
    fig.add_trace(go.Scatter(x=times, y=ch1, mode="lines", name="Channel 2", line=dict(color="#ef4444", width=2)))
    fig.add_trace(go.Scatter(x=times, y=ch2, mode="lines", name="Channel 3", line=dict(color="#a855f7", width=2)))

    fig.add_hline(y=cfg["setpoint"], line_dash="dot", line_color="#ef4444", line_width=1)
    fig.add_hline(y=cfg["lower_bound"], line_dash="dot", line_color="#f59e0b", line_width=1)
    fig.add_hline(y=cfg["upper_bound"], line_dash="dot", line_color="#8b5cf6", line_width=1)

    fig.update_layout(
        height=GRAPH_HEIGHT,
        margin=dict(l=8, r=8, t=24, b=8),
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter, system-ui, sans-serif", color="#374151", size=12),
        xaxis=dict(title=None, showgrid=True, gridcolor="#eef2f7", zeroline=False),
        yaxis=dict(
            title="Temperature (°C)",
            showgrid=True,
            gridcolor="#eef2f7",
            zeroline=False,
            range=[cfg["y_min"], cfg["y_max"]],
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="left", x=0),
    )
    return fig


loaded_cfg = load_config()

app.layout = html.Div(
    className="app-shell",
    children=[
        dcc.Store(id="data-store", data={"times": [], "ch0": [], "ch1": [], "ch2": []}),
        dcc.Store(id="recording-store", data={"active": False, "filename": None}),
        dcc.Store(id="save-file-store", data={"filename": None, "content": ""}),
        dcc.Interval(
            id="interval",
            interval=int(1000 / max(0.1, loaded_cfg.get("sampling_frequency", 1.0))),
            n_intervals=0,
        ),

        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Save current configuration?")),
                dbc.ModalBody("Save As will save the latest recording and the current furnace configuration."),
                dbc.ModalFooter(
                    [
                        dbc.Button("Cancel", id="save-modal-cancel", color="secondary", className="me-2"),
                        dbc.Button("Save Recording + Config", id="save-modal-confirm", color="primary"),
                    ]
                ),
            ],
            id="save-modal",
            is_open=False,
            backdrop="static",
            keyboard=False,
        ),

        html.Div(
            className="topbar",
            children=[
                html.Div(
                    className="brand",
                    children=[
                        html.Div(className="brand-mark", children="T"),
                        html.Div(
                            children=[
                                html.Div("Thermocouple Monitor", className="brand-title"),
                                html.Div(id="machine-label", className="brand-subtitle"),
                            ]
                        ),
                    ],
                ),
                html.Div(
                    className="topbar-actions",
                    children=[
                        html.Div(id="status-indicator", className="status-pill status-ok", children="Connected"),
                        html.Div(id="clock", className="clock"),
                    ],
                ),
            ],
        ),

        html.Div(
            className="ccam-hero",
            children=[
                html.Div(
                    className="ccam-hero-content",
                    children=[
                        html.Div("Thermocouple Monitor", className="ccam-hero-title"),
                        html.Div(
                            "Commonwealth Center for Advanced Manufacturing • Real-time furnace monitoring and recording",
                            className="ccam-hero-subtitle",
                        ),
                    ],
                )
            ],
        ),

        html.Div(
            id="data-mode-banner",
            className="data-mode-banner data-mode-live",
            children="Live hardware data",
        ),

        html.Div(
            className="dashboard-grid",
            children=[
                html.Main(
                    className="main-pane",
                    children=[
                        html.Section(
                            className="panel chart-panel",
                            children=[
                                html.Div(
                                    className="panel-header",
                                    children=[
                                        html.Div(
                                            children=[
                                                html.H2("Live Temperature Chart", className="panel-title"),
                                                html.Div("Real-time temperatures from MCC E-TC", className="panel-subtitle"),
                                            ]
                                        ),
                                        html.Div(
                                            className="panel-meta",
                                            children=[
                                                html.Div("Window", className="meta-label"),
                                                html.Div(f"{GRAPH_WINDOW_SECONDS}s", className="meta-value"),
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                dbc.Label("Y-Axis Min (°C)", className="field-label"),
                                                dbc.Input(
                                                    id="cfg-ymin",
                                                    type="number",
                                                    value=loaded_cfg.get("y_min", DEFAULT_CONFIG["y_min"]),
                                                    step=1,
                                                    className="field-input",
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            [
                                                dbc.Label("Y-Axis Max (°C)", className="field-label"),
                                                dbc.Input(
                                                    id="cfg-ymax",
                                                    type="number",
                                                    value=loaded_cfg.get("y_max", DEFAULT_CONFIG["y_max"]),
                                                    step=1,
                                                    className="field-input",
                                                ),
                                            ]
                                        ),
                                    ],
                                    style={
                                        "display": "grid",
                                        "gridTemplateColumns": "1fr 1fr",
                                        "gap": "12px",
                                        "marginBottom": "12px",
                                    },
                                ),
                                dcc.Graph(
                                    id="live-graph",
                                    figure=make_figure({"times": [], "ch0": [], "ch1": [], "ch2": []}, loaded_cfg),
                                    config={"displayModeBar": False, "responsive": True},
                                    className="live-graph",
                                ),
                                html.Div(
                                    className="temperature-cards",
                                    children=[
                                        html.Div(
                                            className="temp-card",
                                            children=[
                                                html.Div("Channel 1", className="temp-label"),
                                                html.Div(id="temp-0", className="temp-value temp-blue", children="--"),
                                            ],
                                        ),
                                        html.Div(
                                            className="temp-card",
                                            children=[
                                                html.Div("Channel 2", className="temp-label"),
                                                html.Div(id="temp-1", className="temp-value temp-red", children="--"),
                                            ],
                                        ),
                                        html.Div(
                                            className="temp-card",
                                            children=[
                                                html.Div("Channel 3", className="temp-label"),
                                                html.Div(id="temp-2", className="temp-value temp-purple", children="--"),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Section(
                            className="panel recording-panel",
                            children=[
                                html.Div(
                                    className="panel-header",
                                    children=[
                                        html.Div(
                                            children=[
                                                html.H2("Recording", className="panel-title"),
                                                html.Div("Capture a TUS log for later analysis", className="panel-subtitle"),
                                            ]
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="action-row",
                                    children=[
                                        dbc.Button("Start Recording", id="btn-start", color="dark", className="action-btn", n_clicks=0),
                                        dbc.Button(
                                            "Stop Recording",
                                            id="btn-stop",
                                            color="light",
                                            className="action-btn action-btn-secondary",
                                            n_clicks=0,
                                            disabled=True,
                                        ),
                                        dbc.Button("Save As...", id="btn-save-as", color="primary", className="action-btn", n_clicks=0),
                                    ],
                                ),
                                html.Div(id="rec-status", className="status-line", children="Status: Idle"),
                                html.Div(id="rec-file", className="muted-line"),
                                html.Div(id="save-status", className="muted-line"),
                            ],
                        ),
                    ],
                ),
                html.Aside(
                    className="sidebar",
                    children=[
                        html.Section(
                            className="panel sidebar-panel",
                            children=[
                                html.H3("Saved Profiles", className="side-title"),
                                dcc.Dropdown(
                                    id="profile-select",
                                    options=list_profile_options(),
                                    value=None,
                                    placeholder="Select a furnace profile",
                                    clearable=True,
                                ),
                                html.Div(id="profile-status", className="muted-line mt-3"),
                            ],
                        ),
                        html.Section(
                            className="panel sidebar-panel",
                            children=[
                                html.H3("Furnace Profile", className="side-title"),
                                dbc.Label("Furnace Number", className="field-label"),
                                dbc.Input(
                                    id="cfg-furnace",
                                    type="number",
                                    value=loaded_cfg.get("furnace_number", DEFAULT_CONFIG["furnace_number"]),
                                    min=1,
                                    step=1,
                                    className="field-input",
                                ),
                            ],
                        ),
                        html.Section(
                            className="panel sidebar-panel",
                            children=[
                                html.H3("Temperature Bounds", className="side-title"),
                                dbc.Label("Setpoint (°C)", className="field-label"),
                                dbc.Input(
                                    id="cfg-setpoint",
                                    type="number",
                                    value=loaded_cfg.get("setpoint", DEFAULT_CONFIG["setpoint"]),
                                    step=0.1,
                                    className="field-input",
                                ),
                                dbc.Label("Lower Bound (°C)", className="field-label mt-3"),
                                dbc.Input(
                                    id="cfg-lower",
                                    type="number",
                                    value=loaded_cfg.get("lower_bound", DEFAULT_CONFIG["lower_bound"]),
                                    step=0.1,
                                    className="field-input",
                                ),
                                dbc.Label("Upper Bound (°C)", className="field-label mt-3"),
                                dbc.Input(
                                    id="cfg-upper",
                                    type="number",
                                    value=loaded_cfg.get("upper_bound", DEFAULT_CONFIG["upper_bound"]),
                                    step=0.1,
                                    className="field-input",
                                ),
                            ],
                        ),
                        html.Section(
                            className="panel sidebar-panel",
                            children=[
                                html.H3("Sampling", className="side-title"),
                                dbc.Label("Sampling Frequency (Hz)", className="field-label"),
                                dbc.Input(
                                    id="cfg-sampling",
                                    type="number",
                                    value=loaded_cfg.get("sampling_frequency", DEFAULT_CONFIG["sampling_frequency"]),
                                    min=0.1,
                                    step=0.1,
                                    className="field-input",
                                ),
                                html.Div(
                                    "Supports values below 1 Hz, such as 0.5 or 0.2.",
                                    className="muted-line mt-2",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),

        html.Footer(
            className="footer",
            children=[
                html.Div("Thermocouple Dashboard v2.0", className="footer-left"),
                html.Div(id="device-info", className="footer-right"),
            ],
        ),
    ],
)


@app.callback(
    Output("interval", "interval"),
    Input("cfg-sampling", "value"),
)
def update_interval_from_sampling(sampling):
    """Convert a sampling frequency in hertz to a Dash interval."""

    hz = float(sampling) if sampling not in (None, "") else DEFAULT_CONFIG["sampling_frequency"]
    hz = max(0.1, hz)
    return int(1000 / hz)


@app.callback(
    [
        Output("cfg-furnace", "value"),
        Output("cfg-setpoint", "value"),
        Output("cfg-lower", "value"),
        Output("cfg-upper", "value"),
        Output("cfg-ymin", "value"),
        Output("cfg-ymax", "value"),
        Output("cfg-sampling", "value"),
        Output("profile-status", "children"),
    ],
    Input("profile-select", "value"),
    prevent_initial_call=True,
)
def load_selected_profile(profile_filename):
    """Populate dashboard controls from the selected profile."""

    if not profile_filename:
        raise PreventUpdate

    cfg = load_profile_file(profile_filename)
    furnace = cfg.get("furnace_number", DEFAULT_CONFIG["furnace_number"])

    return (
        furnace,
        cfg.get("setpoint", DEFAULT_CONFIG["setpoint"]),
        cfg.get("lower_bound", DEFAULT_CONFIG["lower_bound"]),
        cfg.get("upper_bound", DEFAULT_CONFIG["upper_bound"]),
        cfg.get("y_min", DEFAULT_CONFIG["y_min"]),
        cfg.get("y_max", DEFAULT_CONFIG["y_max"]),
        cfg.get("sampling_frequency", DEFAULT_CONFIG["sampling_frequency"]),
        f"Loaded Furnace {int(furnace)}",
    )


@app.callback(
    [
        Output("temp-0", "children"),
        Output("temp-1", "children"),
        Output("temp-2", "children"),
        Output("live-graph", "figure"),
        Output("data-store", "data"),
        Output("status-indicator", "children"),
        Output("status-indicator", "className"),
        Output("machine-label", "children"),
        Output("clock", "children"),
        Output("device-info", "children"),
        Output("data-mode-banner", "children"),
        Output("data-mode-banner", "className"),
        Output("rec-status", "children"),
        Output("rec-file", "children"),
        Output("recording-store", "data"),
    ],
    Input("interval", "n_intervals"),
    State("cfg-furnace", "value"),
    State("cfg-setpoint", "value"),
    State("cfg-lower", "value"),
    State("cfg-upper", "value"),
    State("cfg-ymin", "value"),
    State("cfg-ymax", "value"),
    State("cfg-sampling", "value"),
    State("data-store", "data"),
    State("recording-store", "data"),
)
def update_temps(n, furnace, setpoint, lower, upper, y_min, y_max, sampling, store, rec_data):
    """Refresh the dashboard with new temperature readings.

    The callback updates display values, graph data, hardware status, and
    appends a row to the active recording file when recording is enabled.
    """

    now_dt = datetime.now()
    now = now_dt.strftime("%H:%M:%S")
    safe_temps = read_live_temps()

    store = store or {"times": [], "ch0": [], "ch1": [], "ch2": []}
    times = store.get("times", [])
    ch0 = store.get("ch0", [])
    ch1 = store.get("ch1", [])
    ch2 = store.get("ch2", [])

    live_cfg = build_live_cfg(furnace, setpoint, lower, upper, y_min, y_max, sampling)

    if any(v is not None for v in safe_temps):
        times.append(now)
        ch0.append(safe_temps[0])
        ch1.append(safe_temps[1])
        ch2.append(safe_temps[2])

        hz = max(0.1, live_cfg["sampling_frequency"])
        max_points = max(20, int(GRAPH_WINDOW_SECONDS * hz))

        times = times[-max_points:]
        ch0 = ch0[-max_points:]
        ch1 = ch1[-max_points:]
        ch2 = ch2[-max_points:]

    new_store = {"times": times, "ch0": ch0, "ch1": ch1, "ch2": ch2}
    fig = make_figure(new_store, live_cfg)

    if getattr(hardware, "simulation_mode", False):
        status_text = "Simulation / MCC board not detected"
        status_class = "status-pill status-warn"
        banner_text = "Simulation mode — live MCC hardware not detected"
        banner_class = "data-mode-banner data-mode-sim"
    else:
        status_text = "Connected"
        status_class = "status-pill status-ok"
        banner_text = "Live hardware data"
        banner_class = "data-mode-banner data-mode-live"

    footer_info = (
        f"Board {hardware.board_num} • IP {hardware.device_ip or 'local'}"
        f" • {'Simulation' if getattr(hardware, 'simulation_mode', False) else 'Live'}"
    )

    if rec_data and rec_data.get("active") and rec_data.get("filename") and any(v is not None for v in safe_temps):
        filepath = RECORDINGS_DIR / rec_data["filename"]
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(
                f"{float(now_dt.hour):.3f}\t"
                f"{float(now_dt.minute):.3f}\t"
                f"{(now_dt.second + now_dt.microsecond / 1_000_000):.3f}\t"
                f"{(safe_temps[0] if safe_temps[0] is not None else 0.0):.3f}\t"
                f"{(safe_temps[1] if safe_temps[1] is not None else 0.0):.3f}\t"
                f"{(safe_temps[2] if safe_temps[2] is not None else 0.0):.3f}\t"
                f"0.000\n"
            )

    rec_status = "Status: Recording" if rec_data and rec_data.get("active") else "Status: Idle"
    rec_file = f"File: {rec_data.get('filename')}" if rec_data and rec_data.get("filename") else ""

    return (
        fmt_temp(safe_temps[0]),
        fmt_temp(safe_temps[1]),
        fmt_temp(safe_temps[2]),
        fig,
        new_store,
        status_text,
        status_class,
        f"Furnace {live_cfg['furnace_number']}",
        now,
        footer_info,
        banner_text,
        banner_class,
        rec_status,
        rec_file,
        rec_data or {"active": False, "filename": None},
    )


@app.callback(
    [
        Output("btn-start", "disabled"),
        Output("btn-stop", "disabled"),
        Output("rec-status", "children"),
        Output("rec-file", "children"),
        Output("recording-store", "data"),
    ],
    Input("btn-start", "n_clicks"),
    Input("btn-stop", "n_clicks"),
    State("cfg-furnace", "value"),
    State("recording-store", "data"),
    prevent_initial_call=True,
)
def handle_recording(start_n, stop_n, furnace, rec_data):
    """Start or stop TUS recording based on the triggering button."""

    if not ctx.triggered_id:
        raise PreventUpdate

    rec_data = rec_data or {"active": False, "filename": None}
    button = ctx.triggered_id

    if button == "btn-start":
        timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
        filename = f"TUS_F{int(furnace or 1)}_{timestamp}.txt"
        filepath = RECORDINGS_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# TUS Recording\n")
            f.write("# Hour\tMinute\tSecond\tChannel1\tChannel2\tChannel3\tReserved\n")
        rec_data["active"] = True
        rec_data["filename"] = filename
        return True, False, "Status: Recording", f"File: {filename}", rec_data

    if button == "btn-stop":
        rec_data["active"] = False
        filename = rec_data.get("filename", "unknown")
        return False, True, "Status: Idle", f"Saved: {filename}", rec_data

    raise PreventUpdate


@app.callback(
    Output("save-modal", "is_open"),
    Input("btn-save-as", "n_clicks"),
    Input("save-modal-cancel", "n_clicks"),
    Input("save-modal-confirm", "n_clicks"),
    State("save-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_save_modal(btn_save, btn_cancel, btn_confirm, is_open):
    """Open or close the Save As confirmation modal."""

    trigger = ctx.triggered_id
    if trigger == "btn-save-as":
        return True
    if trigger in ("save-modal-cancel", "save-modal-confirm"):
        return False
    return is_open


@app.callback(
    [
        Output("save-file-store", "data"),
        Output("profile-select", "options"),
    ],
    Input("save-modal-confirm", "n_clicks"),
    State("cfg-furnace", "value"),
    State("cfg-setpoint", "value"),
    State("cfg-lower", "value"),
    State("cfg-upper", "value"),
    State("cfg-ymin", "value"),
    State("cfg-ymax", "value"),
    State("cfg-sampling", "value"),
    prevent_initial_call=True,
)
def prepare_save_as_with_config(n, furnace, setpoint, lower, upper, y_min, y_max, sampling):
    """Prepare the latest recording and persist the active profile."""

    files = sorted(RECORDINGS_DIR.glob("TUS_*.txt"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not files:
        return {"filename": None, "content": ""}, list_profile_options()

    cfg = build_live_cfg(furnace, setpoint, lower, upper, y_min, y_max, sampling)
    save_config(cfg)

    profile_name = f"furnace_{int(cfg['furnace_number'])}"
    profile_manager.save_profile(profile_name, cfg)

    latest = files[0]
    with open(latest, "r", encoding="utf-8") as f:
        content = f.read()

    return {"filename": latest.name, "content": content}, list_profile_options()


clientside_callback(
    """
    async function(fileData) {
        if (!fileData || !fileData.content) {
            return "No recording file available.";
        }

        const content = fileData.content || "";
        const filename = fileData.filename || "thermocouple_recording.txt";

        try {
            if (window.showSaveFilePicker) {
                const handle = await window.showSaveFilePicker({
                    suggestedName: filename,
                    types: [
                        {
                            description: "Text files",
                            accept: { "text/plain": [".txt"] }
                        }
                    ]
                });

                const writable = await handle.createWritable();
                await writable.write(content);
                await writable.close();
                return "Recording and furnace configuration saved successfully.";
            }
        } catch (err) {
            if (err && err.name === "AbortError") {
                return "Save cancelled.";
            }
        }

        const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);

        return "Chrome Save As was unavailable, so the file was downloaded instead.";
    }
    """,
    Output("save-status", "children"),
    Input("save-file-store", "data"),
    prevent_initial_call=True,
)


if __name__ == "__main__":
    if not hardware.connected:
        hardware.connect()
        if not hardware.connected:
            print("Warning: Could not connect to hardware. Using simulated data.")
    print("Starting Thermocouple Dashboard at http://0.0.0.0:8050/")
    app.run(debug=False, use_reloader=False, host="0.0.0.0", port=8050)
