# ServoPilot — Complete Architecture Document

> **Project**: ServoPilot — Desktop Servo Motor Management Application  
> **Stack**: Python 3 · PySide6 (Qt 6) · pyqtgraph · pyserial · FastAPI · uvicorn  
> **Purpose**: Professional-grade tool for managing, tuning, and choreographing ST3215 servo motors over a serial (RS-485/TTL) bus  

---

## Table of Contents

1. [High-Level Architecture Diagram](#1-high-level-architecture-diagram)
2. [Detailed Module Breakdown](#2-detailed-module-breakdown)
3. [Feature-to-Code Map](#3-feature-to-code-map)
4. [Technologies Used](#4-technologies-used)
5. [Data Flow Deep-Dives](#5-data-flow-deep-dives)
6. [Threading & Concurrency Model](#6-threading--concurrency-model)
7. [Error Handling Strategy](#7-error-handling-strategy)
8. [External Integrations](#8-external-integrations)
9. [File Tree](#9-file-tree)

---

## 1. High-Level Architecture Diagram

```mermaid
graph TB
    subgraph "Entry Point"
        MAIN["main.py<br/>QApplication bootstrap"]
    end

    subgraph "UI Layer — PySide6 / Qt 6"
        MW["main_window.py<br/>ServoPilotMainWindow"]
        
        subgraph "Tab Widgets"
            MON["MonitorTab<br/>Live telemetry dashboard"]
            GRA["GraphTab<br/>Multi-trace plotter"]
            PID["PIDTab<br/>PID tuning + advisor"]
            CTL["ControlTableTab<br/>Register map viewer"]
            FW["FirmwareTab<br/>Device configuration"]
            MP["MotionProfileTab<br/>Waypoint editor"]
            SYNC["SyncTab<br/>Group sync control"]
        end

        subgraph "Dock Panels"
            SLP["ServoListPanel<br/>Port/servo discovery"]
            PC["PacketConsole<br/>Hex packet logger"]
        end

        STYLE["styles/dark_theme.py<br/>QSS stylesheet"]
    end

    subgraph "Backend Layer — Threading Bridge"
        SB["ServoBackend<br/>Qt signal/slot API"]
        HW["_HardwareWorker<br/>QThread worker"]
        TW["TelemetryWorker<br/>Periodic poller"]
    end

    subgraph "API Layer — FastAPI"
        AB["ApiBridge<br/>Thread-safe data bridge"]
        AS["ApiServer<br/>REST + WebSocket"]
    end

    subgraph "Driver Layer — st3215 Package"
        ST["ST3215<br/>High-level servo API"]
        PPH["protocol_packet_handler<br/>Packet construction"]
        PH["PortHandler<br/>pyserial wrapper"]
        GSR["GroupSyncRead"]
        GSW["GroupSyncWrite"]
        VAL["values.py<br/>Constants & registers"]
    end

    subgraph "Hardware"
        BUS["RS-485 / TTL Serial Bus"]
        SERVO["ST3215 Servo Motors"]
    end

    subgraph "External Clients"
        REST["REST Client"]
        WS["WebSocket Client"]
    end

    MAIN --> MW
    MW --> MON & GRA & PID & CTL & FW & MP & SYNC
    MW --> SLP & PC
    STYLE -.->|stylesheet| MW

    SLP -->|connect/scan signals| MW
    MON -->|goal/torque signals| MW
    GRA -->|start/stop signals| MW
    PID -->|read/write PID signals| MW
    CTL -->|read/write register signals| MW
    FW -->|ID/baud/limits signals| MW
    MP -->|execute/stop signals| MW
    SYNC -->|sync_write/home signals| MW
    PC -->|raw_send signal| MW

    MW -->|slots| SB
    SB -->|invokeMethod| HW
    HW -->|signals| SB
    SB -->|signals| MW
    TW -->|read_telemetry| SB

    MW -->|toggle| AS
    AS <-->|shared state| AB
    MW <-->|data sync| AB

    HW --> ST
    ST --> PPH
    PPH --> PH
    ST --> GSR & GSW
    GSR & GSW --> PPH
    PH --> BUS
    BUS --> SERVO

    REST -->|HTTP| AS
    WS -->|WebSocket| AS
```

### Layer Summary

| Layer | Role | Key Technologies |
|-------|------|-----------------|
| **Entry Point** | Bootstrap Qt app, set high-DPI, launch event loop | PySide6 `QApplication` |
| **UI Layer** | 7 tab widgets + 2 dock panels composing the full GUI | PySide6, pyqtgraph |
| **Backend Layer** | Thread-safe bridge between UI and hardware | `QThread`, `QMetaObject.invokeMethod` |
| **API Layer** | Remote control via REST and WebSocket | FastAPI, uvicorn, threading |
| **Driver Layer** | Low-level serial packet protocol for ST3215 servos | pyserial, custom protocol |
| **Hardware** | Physical servo bus and motors | RS-485/TTL @ 38.4K–1Mbps |

---

## 2. Detailed Module Breakdown

### 2.1 Entry Point

#### [main.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/main.py) — 38 lines
Application bootstrap. Enables high-DPI scaling (`AA_EnableHighDpiScaling`), creates the `QApplication`, instantiates [ServoPilotMainWindow](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/main_window.py#26-558), maximizes it, and enters the Qt event loop. Clean exit via `sys.exit(app.exec())`.

---

### 2.2 Main Window — Orchestrator

#### [main_window.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/main_window.py) — 558 lines

The central nervous system of the application. [ServoPilotMainWindow(QMainWindow)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/main_window.py#26-558) wires together every component:

| Responsibility | Details |
|---|---|
| **Tab creation** | Builds 7 tabs: Monitor · Graph · PID Tuning · Control Table · Firmware · Motion Profile · Sync Control |
| **Dock panels** | Left dock: [ServoListPanel](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/servo_list_panel.py#24-253) (port/servo discovery). Bottom dock: [PacketConsole](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/packet_console.py#12-96) (collapsible hex logger). |
| **Menu bar** | File → Exit, View → toggle Console/Servo List, Help → About |
| **Status bar** | Persistent E-Stop button, API toggle switch, connection status label |
| **Signal wiring** | ~50 signal→slot connections linking widget signals to [ServoBackend](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/servo_backend.py#588-764) methods and backend signals back to widget update slots |
| **Backend init** | Creates [ServoBackend](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/servo_backend.py#588-764), [TelemetryWorker](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/telemetry_worker.py#9-59), and optionally `ApiServer` + [ApiBridge](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/api_bridge.py#16-143) |
| **E-Stop** | Emergency stop button disabling torque on all servos instantly |

---

### 2.3 Backend Package — [backend/](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/main_window.py#203-220)

#### [servo_backend.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/servo_backend.py) — 764 lines

The most critical backend file. Contains two classes:

**[_HardwareWorker(QObject)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/servo_backend.py#93-586)** — lives on a `QThread`, serializes all blocking serial I/O:
- `do_connect(port, baud)` — opens serial port via [ST3215](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#15-591)
- `do_scan()` — pings IDs 0–253 to find connected servos
- `do_read_telemetry(id)` — reads position, velocity, load, voltage, temperature, current, moving status
- `do_write_goal(id, pos)` — sends goal position
- `do_set_torque(id, on)` — enables/disables torque
- `do_write_pid(id, p, i, d)` — EEPROM unlock → write P/I/D → re-lock
- `do_change_id(old, new)` — EEPROM unlock → write new ID → re-lock
- `do_execute_motion_profile(id, waypoints, loop)` — runs waypoint sequence in a background thread
- `do_sync_write(positions_dict)` — sequential write to multiple servos
- `do_read_registers(id)` — reads all control table registers
- `do_emergency_stop(ids)` — disables torque on all specified servos

**[ServoBackend(QObject)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/servo_backend.py#588-764)** — public API for the UI thread. Proxies every method call to [_HardwareWorker](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/servo_backend.py#93-586) via `QMetaObject.invokeMethod(Qt.QueuedConnection)` ensuring thread safety. All results flow back through Qt signals.

**Register Map** (`REGISTERS` constant): 30+ register definitions with address, name, size, access mode (R/RW), and description — covering firmware version, ID, baud, return delay, angle limits, PID gains, torque, goal position, speed, load, voltage, temperature, current, and more.

#### [telemetry_worker.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/telemetry_worker.py) — 59 lines

[TelemetryWorker(QThread)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/telemetry_worker.py#9-59) — periodically calls `ServoBackend.read_telemetry()` for each connected servo at a configurable poll rate (10–50 Hz). Emits `telemetry_update(servo_id, data)` signals consumed by multiple UI widgets simultaneously.

#### [api_bridge.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/api_bridge.py) — 143 lines

[ApiBridge](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/api_bridge.py#16-143) — thread-safe data exchange between the FastAPI server thread and the Qt main thread. Protected by `threading.Lock`. Stores:
- Latest telemetry per servo
- Connected servo list
- Goal position overrides
- Home positions
- Command queue (deque) for async UI → API commands

#### [api_server.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/api_server.py) — 270 lines

`ApiServer` — FastAPI application running in a daemon thread via `uvicorn`. Endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/servos` | List connected servo IDs |
| GET | `/servos/{id}` | Get servo state (position, velocity, load, etc.) |
| POST | `/servos/{id}/position` | Set goal position |
| POST | `/servos/{id}/torque` | Enable/disable torque |
| POST | `/servos/{id}/mode` | Set operating mode |
| POST | `/home` | Home all servos |
| POST | `/estop` | Emergency stop |
| GET | `/groups` | List servo groups |
| POST | `/groups` | Create/update group |
| WS | `/ws/telemetry` | Stream live telemetry via WebSocket |

Includes API key authentication via `X-API-Key` header and CORS middleware.

---

### 2.4 Driver Package — `st3215/`

#### [st3215.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py) — 593 lines

[ST3215(protocol_packet_handler)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#15-591) — high-level servo control API. Key methods:

| Method | Purpose |
|--------|---------|
| [Ping(id)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#30-42) | Check if servo responds |
| [ListServos(max_id)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#44-56) | Scan bus for all servos |
| [MoveTo(id, pos, speed, acc)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#413-458) | Command servo to position |
| `SetTorque(id, on)` | Enable/disable torque |
| [ReadPosition(id)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#496-509) | Read current position |
| `ReadVelocity(id)` | Read current speed |
| [ReadLoad(id)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#58-72) | Read current load % |
| [ReadVoltage(id)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#73-86) | Read supply voltage |
| [ReadTemperature(id)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#101-114) | Read motor temperature |
| [ReadCurrent(id)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#87-100) | Read motor current (mA) |
| [IsMoving(id)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#169-182) | Check if servo is in motion |
| [SetAcceleration(id, acc)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#184-199) | Set acceleration |
| [SetSpeed(id, speed)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#201-216) | Set max speed |
| [SetMode(id, mode)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#247-258) | Set Position/Wheel/PWM/Step mode |
| `UnlockEEPROM(id)` / `LockEEPROM(id)` | EEPROM write protection |
| `ReadPID(id)` | Read P, I, D register values |
| `WritePID(id, p, i, d)` | Write PID gains |
| `ChangeID(id, new_id)` | Change servo bus ID |
| [ChangeBaud(id, code)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#567-591) | Change baud rate code |
| `SetAngleLimits(id, min, max)` | Set rotation bounds |

#### [protocol_packet_handler.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/protocol_packet_handler.py) — 509 lines

Low-level protocol engine. Handles:
- Packet header construction (`FF FF`)
- Checksum calculation (bitwise complement of sum)
- [txPacket()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/protocol_packet_handler.py#97-130) / [rxPacket()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/group_sync_read.py#55-75) — transmit and receive with timeout
- [read1ByteTxRx()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/protocol_packet_handler.py#336-340), [read2ByteTxRx()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/protocol_packet_handler.py#349-353), [read4ByteTxRx()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/protocol_packet_handler.py#363-368) — typed register reads
- [write1ByteTxRx()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/protocol_packet_handler.py#401-404), [write2ByteTxRx()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/protocol_packet_handler.py#409-412) — typed register writes
- [syncReadTx()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/protocol_packet_handler.py#456-471) / [syncWriteTxOnly()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/protocol_packet_handler.py#494-509) — bulk operations

#### [port_handler.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/port_handler.py) — 95 lines

[PortHandler](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/port_handler.py#8-94) — wraps `pyserial.Serial`. Manages port open/close, [readPort(length)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/port_handler.py#42-47), [writePort(data)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/port_handler.py#48-50), and dynamic packet timeout calculation based on baud rate and data length.

#### [group_sync_read.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/group_sync_read.py) — 150 lines

[GroupSyncRead](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/group_sync_read.py#3-150) — reads the same register range from multiple servos in one bus transaction. Manages per-servo parameter storage and parses interleaved response packets.

#### [group_sync_write.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/group_sync_write.py) — 72 lines

[GroupSyncWrite](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/group_sync_write.py#3-72) — writes different values to the same register on multiple servos simultaneously. Constructs a single sync-write packet for bus efficiency.

#### [values.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/values.py) — 110 lines

Constants and enumerations:
- Packet structure bytes (`HEADER`, `BROADCASTING_ID`)
- Instruction codes (`INST_PING`, `INST_READ`, `INST_WRITE`, `INST_SYNC_READ`, `INST_SYNC_WRITE`, etc.)
- Register addresses (`ADDR_ID`, `ADDR_BAUD`, `ADDR_GOAL_POSITION`, `ADDR_P_COEFF`, etc.)
- Communication result codes (`COMM_SUCCESS`, `COMM_TX_FAIL`, `COMM_RX_TIMEOUT`, etc.)

---

### 2.5 UI Widgets — [widgets/](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/main_window.py#222-278)

#### [servo_list_panel.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/servo_list_panel.py) — 253 lines

Left dock widget. Features:
- **Port selector**: Auto-refreshes COM port list every 2s via `serial.tools.list_ports`
- **Baud selector**: 7 baud rate options (38.4K–1M)
- **Connect/Disconnect** buttons with connection status indicator
- **Scan** button (IDs 0–253)
- **Servo table**: 7 columns (ID, Model, FW, Baud, Temp, Volt, Status) with colour-coded temperature (green < 55°C < yellow < 70°C < red)

Signals: [servo_selected(int)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/main_window.py#363-372), `connect_requested(str, int)`, `disconnect_requested()`, `scan_requested()`

#### [monitor_tab.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/monitor_tab.py) — 329 lines

Tab 1 — Live telemetry dashboard. Features:
- 6 LCD panels: Position, Velocity, Load, Voltage, Temperature, Current
- Moving indicator (●)
- Goal Position control: slider (0–4095) + spinbox + "Send ▶" button
- Motor Control: Speed (step/s), Acceleration, Mode selector (Position/Wheel/PWM/Step)
- Torque ON/OFF toggle with per-servo state memory
- Torque-not-enabled warning flash when trying to move without torque
- Poll rate selector (10/20/30/50 Hz)

Signals: `goal_position_changed`, `goal_speed_changed`, `acceleration_changed`, [torque_toggled](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/monitor_tab.py#314-329), `mode_changed`, `rate_changed`

#### [graph_tab.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/graph_tab.py) — 401 lines

Tab 2 — Real-time multi-trace plotter. Features:
- **Metric toggles**: Position, Goal Position, Velocity, Load, Voltage, Temperature, Current  
- **Multi-servo overlay**: Ctrl+click to plot multiple servos; hue-shifted curves for distinguishability
- **Time window slider**: 5–60s rolling window
- **Performance optimization**: Timer-based repaint at ~12fps (`_REPAINT_MS=80`), numpy array filtering, dirty-flag pattern
- **CSV export**: Wide-format CSV with computed error column (`goal - position`), header comments, per-servo export
- **Start/Stop/Clear** controls

Data storage: `deque(maxlen=10_000)` per metric per servo.

#### [pid_tab.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/pid_tab.py) — 929 lines

Tab 3 — PID tuning with live step-response analysis. The most complex widget. Features:

- **Servo selector** combo box for targeting specific servos
- **P/I/D spinboxes** (0–255) with descriptive tooltips
- **Read from Servo / Write to EEPROM** buttons
- **Restore Defaults** (P=32, I=0, D=16)
- **Live step-response graph**: Actual vs Goal curves with settle-band region overlay
- **Trigger Step Test**: +200 step impulse for measurable response
- **Step Response Metrics** (auto-computed):
  - Peak Overshoot (%) — measured only PAST the goal after crossing
  - Settling Time (s) — ±5% band, 300ms dwell requirement
  - Steady-State Error (steps) — computed post-settle only
- **Tuning Advisor** — rule-based engine that analyses metrics and suggests PID adjustments:
  - Oscillation detection (3+ goal crossings)
  - High/moderate overshoot → decrease P, increase D
  - Sluggish response → increase P (only when overshoot is safe)
  - Steady-state error → increase I (capped at I=10 for ST3215)
  - "Apply" button stages suggested values into spinboxes

Algorithm constants: `STEP_THRESHOLD=20`, `SETTLE_BAND_PCT=5%`, `SETTLE_DURATION=0.30s`, `SS_WINDOW=1.0s`

#### [control_table_tab.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/control_table_tab.py) — 172 lines

Tab 4 — Full register map viewer/editor. Features:
- 5-column table: Address (hex), Name, Value, Access (R/RW), Description
- Read-only registers shown with greyed styling
- RW registers are double-click editable
- Row background colour-coded by access type
- "Read All" and "Write Selected" buttons
- Monospace font (`Consolas`) for register values

#### [firmware_tab.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/firmware_tab.py) — 254 lines

Tab 5 — Device configuration. Three-column layout:

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Change Servo ID (with confirmation dialog) | Angle Limits (min/max 0–4095) | Servo Information panel |
| Change Bus Baudrate (8 options) | Position Offset / Tare (-2047 to +2047) | ID, Model, FW, Mode, Temp, Voltage, Status |

All writes include EEPROM unlocking/re-locking and safety confirmation dialogs.

#### [motion_profile_tab.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/motion_profile_tab.py) — 774 lines

Tab 6 — Waypoint trajectory editor. Features:
- **Target selector**: Individual servo OR group from Sync tab
- **Dynamic table columns**: Single-servo (Position/Speed/Accel/Delay) or multi-servo (per-servo position columns)
- **Row editing**: Add, Duplicate, Remove, Move Up/Down, Swap
- **Trajectory preview graph**: pyqtgraph with one curve per servo (colour-coded)
- **Execute/Stop controls** with loop option
- **Save/Load**: JSON for multi-servo profiles, CSV for single-servo
- **Load Python scripts**: Parses `SERVO_IDS` and `WAYPOINTS` variables via `ast.literal_eval`
- **Export Python**: Generates standalone [.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/main.py) script using [ST3215](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#15-591) directly

Signals: `execute_requested(int, list, bool)`, `execute_group_requested(list, list, bool)`, `stop_requested()`

#### [sync_tab.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/sync_tab.py) — 787 lines

Tab 7 — Servo group control. Features:
- **Group management**: Create/rename/delete named groups (e.g., "Left Arm")
- **Servo assignment**: Checkbox panel to assign servos to groups
- **Position editor**: Per-servo slider (0–4095) + spinbox + degree label + "Read Current" button
- **Sync Move**: Fires all positions in one hardware sync-write packet
- **Homing system**:
  - Per-servo home position spinboxes
  - Enable/disable per servo
  - "Set Current as Home" (reads live positions)
  - "Home All Servos" with moving-safety dialog
  - Persistent storage in [home_pose.json](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/home_pose.json)
- **Stop Group**: Disables torque on all group members

#### [packet_console.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/packet_console.py) — 96 lines

Bottom dock — Hex packet logger. Features:
- Raw hex packet sender (ID spinbox + hex input field)
- Timestamped, colour-coded log (TX=orange, RX=blue, Error=red, OK=green)
- Monospace font, auto-scroll, Clear button

---

### 2.6 Styling — [styles/](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/styles/dark_theme.py#4-643)

#### [dark_theme.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/styles/dark_theme.py) — 661 lines

[get_stylesheet()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/styles/dark_theme.py#4-643) → 640-line QSS string with:
- Dark background palette (`#0d1117`, `#161b22`, `#21262d`)
- Button variants: `btn_success` (green), `btn_danger` (red), `btn_warn` (orange), `btn_flat` (minimal)
- Styled tabs, scrollbars, sliders, spinboxes, combo boxes, group boxes, LCD numbers
- Accent colour constants exported: `ACCENT_CYAN`, `ACCENT_GREEN`, `ACCENT_ORANGE`, `ACCENT_RED`, `ACCENT_PURPLE`, `ACCENT_YELLOW`
- `TRACE_COLORS` dict mapping metric names to graph line colours

---

### 2.7 Configuration & Packaging

| File | Purpose |
|------|---------|
| [requirements.txt](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/requirements.txt) | `PySide6`, `pyqtgraph`, `pyserial` |
| [setup.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/setup.py) | Package metadata for `st3215` library distribution |
| [setup.cfg](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/setup.cfg) | Bumpversion and setuptools config |
| [home_pose.json](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/home_pose.json) | Persisted home positions per servo |
| [.gitignore](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/.gitignore) | Excludes `__pycache__`, `.venv`, IDE files, builds |

---

### 2.8 Test Suite — [test/](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/pid_tab.py#912-922)

12 standalone test scripts for direct hardware validation (run independently, not pytest):

| Script | Tests |
|--------|-------|
| [test_01_ping_servo.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/test/test_01_ping_servo.py) | Basic servo connectivity |
| [test_02_list_servos.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/test/test_02_list_servos.py) | Bus scan |
| [test_03_read_load_voltage_current.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/test/test_03_read_load_voltage_current.py) | Electrical telemetry |
| [test_04_read_temperature.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/test/test_04_read_temperature.py) | Thermal monitoring |
| [test_05_read_acceleration.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/test/test_05_read_acceleration.py) | Motion parameter read |
| [test_06_read_mode.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/test/test_06_read_mode.py) | Operating mode read |
| [test_07_read_correction.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/test/test_07_read_correction.py) | Position correction/offset |
| [test_08_read_status.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/test/test_08_read_status.py) | Error flags |
| [test_09_is_moving.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/test/test_09_is_moving.py) | Motion detection |
| [test_10_complete_motion_control.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/test/test_10_complete_motion_control.py) | End-to-end movement |
| [test_11_change_baudrate.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/test/test_11_change_baudrate.py) | Baud rate modification |
| [test_12_read_position.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/test/test_12_read_position.py) | Position register read |

---

## 3. Feature-to-Code Map

### 3.1 Connection & Discovery

| Feature | UI Widget | Backend Method | Driver Method |
|---------|-----------|----------------|---------------|
| Select serial port | `ServoListPanel._port_combo` | — | — |
| Connect to port | `ServoListPanel.connect_requested` → `main_window` | `ServoBackend.connect_device()` → `_HW.do_connect()` | [ST3215(port)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#15-591) → `PortHandler.openPort()` |
| Disconnect | `ServoListPanel.disconnect_requested` | `ServoBackend.disconnect()` | `PortHandler.closePort()` |
| Scan for servos | `ServoListPanel.scan_requested` | `_HW.do_scan()` | `ST3215.ListServos(253)` → [Ping(0..253)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#30-42) |
| Auto-refresh ports | `ServoListPanel._port_timer` (2s) | — | `serial.tools.list_ports` |

### 3.2 Live Monitoring

| Feature | UI Widget | Backend | Driver |
|---------|-----------|---------|--------|
| LCD telemetry display | `MonitorTab._pos_lcd`, etc. | [TelemetryWorker](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/telemetry_worker.py#9-59) → `_HW.do_read_telemetry()` | [ReadPosition()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#496-509), `ReadVelocity()`, [ReadLoad()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#58-72), [ReadVoltage()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#73-86), [ReadTemperature()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#101-114), [ReadCurrent()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#87-100), [IsMoving()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#169-182) |
| Moving indicator | `MonitorTab._moving_dot` | `telemetry_update` signal | [IsMoving()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#169-182) |
| Temperature colour-coding | `ServoListPanel.update_telemetry()` | `telemetry_update` signal | [ReadTemperature()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#101-114) |
| Poll rate control | `MonitorTab._rate_combo` → `rate_changed` | `TelemetryWorker.set_rate()` | — |

### 3.3 Servo Control

| Feature | UI Widget | Backend | Driver |
|---------|-----------|---------|--------|
| Set goal position | `MonitorTab._send_pos_btn` | `_HW.do_write_goal()` | `ST3215.MoveTo()` |
| Set speed | `MonitorTab._speed_btn` | `_HW.do_set_speed()` | `ST3215.SetSpeed()` |
| Set acceleration | `MonitorTab._acc_btn` | `_HW.do_set_acceleration()` | `ST3215.SetAcceleration()` |
| Change mode | `MonitorTab._mode_btn` | `_HW.do_set_mode()` | `ST3215.SetMode()` |
| Toggle torque | `MonitorTab._torque_btn` | `_HW.do_set_torque()` | `ST3215.SetTorque()` |
| Torque guard | `MonitorTab._flash_torque_warning()` | — | — |
| Emergency stop | `main_window._estop_btn` | `_HW.do_emergency_stop()` | `SetTorque(id, False)` × N |

### 3.4 Real-Time Graphing

| Feature | Code Location |
|---------|---------------|
| Multi-metric traces | `GraphTab._metric_checks` + `TRACE_COLORS` |
| Multi-servo overlay | `GraphTab._servo_list` (extended selection) + hue shifting |
| Rolling time window | `GraphTab._tw_slider` → `_window` |
| Throttled repaint | `GraphTab._repaint_timer` (80ms) + `_dirty` flag |
| Numpy filtering | `GraphTab._refresh_plot()` — `np.array()` + boolean mask |
| CSV telemetry export | `GraphTab._export_csv()` — wide-format with error column |

### 3.5 PID Tuning

| Feature | Code Location |
|---------|---------------|
| Read PID from servo | `PIDTab._read_pid()` → `ServoBackend.read_pid()` → `ST3215.ReadPID()` |
| Write PID to EEPROM | `PIDTab._write_pid()` → `ServoBackend.write_pid()` → `UnlockEEPROM` → `WritePID` → `LockEEPROM` |
| Step-response graph | `PIDTab._curve_pos` / `_curve_goal` |
| Settle band overlay | `PIDTab._settle_region` (LinearRegionItem) |
| Overshoot detection | `PIDTab._detect_and_track_step()` — tracks goal crossings |
| Settling time | `PIDTab._settled_since` + `SETTLE_DURATION` (300ms dwell) |
| Steady-state error | `PIDTab._ss_error` — post-settle mean |pos − goal| |
| Tuning advisor | `PIDTab._compute_suggestions()` — rule-based engine |
| Step test trigger | `PIDTab._trigger_step_test()` → [step_test_requested](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/main_window.py#414-424) signal |

### 3.6 Register Map

| Feature | Code Location |
|---------|---------------|
| Read all registers | `ControlTableTab._read_all()` → `ServoBackend.read_registers()` |
| Edit RW registers | `ControlTableTab._table` (double-click editing) |
| Write selected | `ControlTableTab._write_selected()` → per-register write |

### 3.7 Device Configuration

| Feature | Code Location |
|---------|---------------|
| Change servo ID | `FirmwareTab._change_id()` → `ServoBackend.change_id()` → `ChangeID()` |
| Change baud rate | `FirmwareTab._change_baud()` → `ServoBackend.change_baud()` → [ChangeBaud()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#567-591) |
| Set angle limits | `FirmwareTab._write_limits()` → `ST3215.SetAngleLimits()` |
| Position offset | `FirmwareTab._write_offset()` → `ST3215.SetPositionOffset()` |

### 3.8 Motion Profiles

| Feature | Code Location |
|---------|---------------|
| Waypoint editing | `MotionProfileTab._table` + add/dup/del/move buttons |
| Trajectory preview | `MotionProfileTab._update_preview()` — pyqtgraph plot |
| Single-servo execute | `execute_requested` → `ServoBackend.execute_motion_profile()` |
| Group execute | `execute_group_requested` → backend group execution |
| JSON save/load | `MotionProfileTab._save_profile()` / [_load_json_profile()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/motion_profile_tab.py#522-567) |
| CSV save/load | Single-servo backward compatibility |
| Python import | [_load_python_profile()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/motion_profile_tab.py#590-671) — `ast.literal_eval` parsing |
| Python export | [_export_python()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/motion_profile_tab.py#674-774) — generates standalone [ST3215](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/st3215/st3215.py#15-591) script |

### 3.9 Sync Control & Homing

| Feature | Code Location |
|---------|---------------|
| Group CRUD | `SyncTab._add_group()` / [_remove_group()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/sync_tab.py#380-398) / [_rename_group()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/sync_tab.py#399-415) |
| Servo assignment | `SyncTab._on_servo_toggled()` → checkbox panel |
| Position sliders | [_ServoRow](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/sync_tab.py#29-120) — slider + spinbox + degree label |
| Sync move | `SyncTab._fire_sync_move()` → [sync_write_requested](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/main_window.py#387-402) → `ServoBackend.sync_write_positions()` |
| Read all current | `SyncTab._read_all_current()` |
| Set all to centre | `SyncTab._set_all_centre()` (2048 = 180°) |
| Stop group | `SyncTab._stop_group()` → `torque_off_requested` |
| Set current as home | `SyncTab._set_current_as_home()` — reads latest telemetry |
| Home all servos | `SyncTab._home_all()` — with moving-safety dialog |
| Home persistence | `SyncTab._save_home_pose()` / [_load_home_pose()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/sync_tab.py#757-774) → [home_pose.json](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/home_pose.json) |

### 3.10 API Server

| Feature | Code Location |
|---------|---------------|
| REST endpoints | [api_server.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/api_server.py) — FastAPI routes |
| WebSocket telemetry | [api_server.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/api_server.py) — `/ws/telemetry` |
| Thread-safe bridge | [api_bridge.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/api_bridge.py) — [ApiBridge](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/api_bridge.py#16-143) with `threading.Lock` |
| API key auth | [api_server.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/api_server.py) — `X-API-Key` header |
| CORS | [api_server.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/api_server.py) — `CORSMiddleware` |
| Toggle on/off | [main_window.py](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/main_window.py) — status bar switch |

### 3.11 Packet Console

| Feature | Code Location |
|---------|---------------|
| Raw hex sender | `PacketConsole._hex_edit` + [_send()](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/widgets/packet_console.py#64-76) |
| Timestamped log | `PacketConsole.append_log()` — colour-coded HTML |
| Collapsible dock | `main_window._console_dock` — View menu toggle |

---

## 4. Technologies Used

| Technology | Version | Role |
|------------|---------|------|
| **Python** | 3.10+ | Core language |
| **PySide6** | ≥ 6.x | Qt 6 bindings — GUI framework |
| **pyqtgraph** | ≥ 0.13 | High-performance scientific plotting |
| **pyserial** | ≥ 3.x | Serial port communication |
| **FastAPI** | ≥ 0.100 | REST/WebSocket API server |
| **uvicorn** | ≥ 0.23 | ASGI server for FastAPI |
| **numpy** | ≥ 1.24 | Array operations for graph filtering |

---

## 5. Data Flow Deep-Dives

### 5.1 Telemetry Data Flow

```
TelemetryWorker (QThread, timer loop)
    │
    ▼
ServoBackend.read_telemetry(servo_id)
    │ QMetaObject.invokeMethod(Qt.QueuedConnection)
    ▼
_HardwareWorker.do_read_telemetry(servo_id)
    │ calls ST3215.ReadPosition(), ReadVelocity(), etc.
    ▼
PortHandler.writePort() → Serial TX
PortHandler.readPort()  → Serial RX
    │
    ▼
_HardwareWorker emits telemetry_read(servo_id, data_dict)
    │ Qt signal (cross-thread)
    ▼
ServoBackend.telemetry_update signal
    │ connected to multiple slots:
    ├──→ MonitorTab.update_telemetry()     → LCD displays
    ├──→ GraphTab.update_telemetry()       → plot data buffers
    ├──→ PIDTab.update_telemetry()         → step-response analysis
    ├──→ ServoListPanel.update_telemetry() → table temp/voltage
    ├──→ FirmwareTab.update_telemetry()    → info panel
    ├──→ SyncTab.update_telemetry()        → movement cache
    └──→ ApiBridge.set_telemetry()         → API distribution
```

### 5.2 Command Data Flow (Goal Position Example)

```
User drags slider in MonitorTab
    │
    ▼
MonitorTab._send_position()
    │ checks torque is enabled
    ▼
MonitorTab.goal_position_changed.emit(servo_id, position)
    │ Qt signal
    ▼
main_window slot → ServoBackend.write_goal_position(id, pos)
    │ QMetaObject.invokeMethod
    ▼
_HardwareWorker.do_write_goal(id, pos)
    │
    ▼
ST3215.MoveTo(id, pos, speed, acc)
    │
    ▼
protocol_packet_handler.write2ByteTxRx(id, ADDR_GOAL_POSITION, pos)
    │
    ▼
PortHandler.writePort(packet_bytes) → Serial TX → Servo moves
```

---

## 6. Threading & Concurrency Model

```mermaid
graph LR
    subgraph "Main Thread (Qt Event Loop)"
        UI["All Widgets<br/>Signal/Slot dispatch"]
    end

    subgraph "Hardware Thread (QThread)"
        HW["_HardwareWorker<br/>Serialized I/O"]
    end

    subgraph "Telemetry Thread (QThread)"
        TW["TelemetryWorker<br/>Periodic polling"]
    end

    subgraph "API Thread (daemon)"
        API["uvicorn + FastAPI"]
    end

    subgraph "Motion Thread (daemon)"
        MOT["Motion profile<br/>execution loop"]
    end

    UI -->|"QMetaObject.invokeMethod<br/>(QueuedConnection)"| HW
    HW -->|"Qt signals<br/>(auto cross-thread)"| UI
    TW -->|calls| HW
    API <-->|"threading.Lock<br/>(ApiBridge)"| UI
    HW -.->|"spawns for profiles"| MOT
```

**Key design decisions**:
- All serial I/O is serialized through a single [_HardwareWorker](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/servo_backend.py#93-586) on one `QThread` — prevents bus contention
- UI never blocks on I/O — all hardware calls use `QMetaObject.invokeMethod` with `Qt.QueuedConnection`
- Telemetry worker is a separate `QThread` with a timer — decoupled from UI frame rate
- Graph repaint is throttled to ~12fps via dirty-flag + timer pattern
- API server runs in a Python `threading.Thread(daemon=True)` with [ApiBridge](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/api_bridge.py#16-143) using `threading.Lock` for shared state

---

## 7. Error Handling Strategy

| Layer | Strategy |
|-------|----------|
| **Driver** | Returns `COMM_*` result codes; caller checks for success |
| **Backend** | Catches exceptions in [_HardwareWorker](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/backend/servo_backend.py#93-586), emits [error(str)](file:///c:/Users/srich/OneDrive/Desktop/ServoPilot/main_window.py#348-352) signal |
| **UI** | Status labels show error messages; `QMessageBox` for critical actions |
| **API** | HTTP error codes (401, 404, 500); WebSocket close on error |
| **Telemetry** | Silent skip on read failure — prevents polling loop crash |
| **EEPROM writes** | Confirmation dialogs before irreversible changes (ID, baud, PID) |
| **Home pose** | Try/except around file I/O — starts fresh if corrupt |

---

## 8. External Integrations

| Integration | Protocol | Purpose |
|-------------|----------|---------|
| **ST3215 Servo Bus** | Custom serial protocol (FF FF header, checksum) | Motor control |
| **REST API** | HTTP/1.1 (FastAPI) | Remote control from external applications |
| **WebSocket** | WS (FastAPI) | Real-time telemetry streaming |
| **File System** | JSON, CSV, Python | Profile persistence, telemetry export |
| **OS Serial Ports** | pyserial | Hardware communication |

---

## 9. File Tree

```
ServoPilot/
├── main.py                          # Entry point (38 lines)
├── main_window.py                   # Main window orchestrator (558 lines)
├── requirements.txt                 # Dependencies
├── setup.py / setup.cfg             # Packaging
├── home_pose.json                   # Homing persistence
├── .gitignore
├── README.md
│
├── backend/
│   ├── __init__.py
│   ├── servo_backend.py             # Threading bridge (764 lines)
│   ├── telemetry_worker.py          # Periodic poller (59 lines)
│   ├── api_bridge.py                # Thread-safe data bridge (143 lines)
│   └── api_server.py                # FastAPI REST + WS (270 lines)
│
├── st3215/
│   ├── __init__.py
│   ├── st3215.py                    # High-level servo API (593 lines)
│   ├── protocol_packet_handler.py   # Packet engine (509 lines)
│   ├── port_handler.py              # pyserial wrapper (95 lines)
│   ├── group_sync_read.py           # Bulk read (150 lines)
│   ├── group_sync_write.py          # Bulk write (72 lines)
│   └── values.py                    # Constants (110 lines)
│
├── widgets/
│   ├── __init__.py
│   ├── servo_list_panel.py          # Port/servo discovery (253 lines)
│   ├── monitor_tab.py               # Live telemetry dashboard (329 lines)
│   ├── graph_tab.py                 # Multi-trace plotter (401 lines)
│   ├── pid_tab.py                   # PID tuning + advisor (929 lines)
│   ├── control_table_tab.py         # Register map viewer (172 lines)
│   ├── firmware_tab.py              # Device configuration (254 lines)
│   ├── motion_profile_tab.py        # Waypoint editor (774 lines)
│   ├── sync_tab.py                  # Group sync control (787 lines)
│   └── packet_console.py            # Hex packet logger (96 lines)
│
├── styles/
│   ├── __init__.py
│   └── dark_theme.py                # QSS stylesheet (661 lines)
│
└── test/
    ├── README.md
    ├── test_01_ping_servo.py
    ├── test_02_list_servos.py
    ├── test_03_read_load_voltage_current.py
    ├── test_04_read_temperature.py
    ├── test_05_read_acceleration.py
    ├── test_06_read_mode.py
    ├── test_07_read_correction.py
    ├── test_08_read_status.py
    ├── test_09_is_moving.py
    ├── test_10_complete_motion_control.py
    ├── test_11_change_baudrate.py
    └── test_12_read_position.py
```

**Total**: ~7,500 lines of application code across 25+ source files.
