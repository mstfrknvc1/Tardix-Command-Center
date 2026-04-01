"""
Hardware sensor reading utilities.

Reads CPU/GPU temperatures and fan RPM via psutil (alienware_wmi /
coretemp / dell_smm hwmon drivers).  No elevated privileges required.
All public functions return None on failure; callers handle gracefully.
"""

try:
    import psutil  # type: ignore
except ImportError:
    psutil = None


# ── helpers ──────────────────────────────────────────────────────────────────

def _sensors_temperatures() -> dict:
    if psutil is None:
        return {}
    try:
        return psutil.sensors_temperatures() or {}
    except Exception:
        return {}


def _sensors_fans() -> dict:
    if psutil is None:
        return {}
    try:
        return psutil.sensors_fans() or {}
    except Exception:
        return {}


# ── public API ────────────────────────────────────────────────────────────────

def read_cpu_temp() -> int | None:
    """Return CPU temperature in °C, or None if unavailable."""
    temps = _sensors_temperatures()

    # Best source for Alienware / Dell G series
    for key in ("alienware_wmi", "dell_ddv"):
        if key in temps:
            entry = next((e for e in temps[key] if "cpu" in e.label.lower()), None)
            if entry:
                return int(entry.current)

    # Intel coretemp (Package id 0)
    if "coretemp" in temps:
        entries = temps["coretemp"]
        pkg = next((e for e in entries if "package" in e.label.lower()), None)
        if pkg:
            return int(pkg.current)
        if entries:
            return int(max(e.current for e in entries))

    # AMD k10temp / zenpower
    for key in ("k10temp", "zenpower"):
        if key in temps and temps[key]:
            tctl = next((e for e in temps[key] if "tctl" in e.label.lower()), None)
            return int(tctl.current if tctl else temps[key][0].current)

    # Generic fallback
    if "acpitz" in temps and temps["acpitz"]:
        return int(temps["acpitz"][0].current)

    return None


def read_gpu_temp() -> int | None:
    """Return GPU temperature in °C, or None if unavailable."""
    temps = _sensors_temperatures()

    for key in ("alienware_wmi", "dell_ddv"):
        if key in temps:
            entry = next(
                (e for e in temps[key]
                 if "gpu" in e.label.lower() or "video" in e.label.lower()),
                None,
            )
            if entry:
                return int(entry.current)

    # amdgpu / nouveau hwmon
    for key in ("amdgpu", "nouveau"):
        if key in temps:
            edge = next((e for e in temps[key] if "edge" in e.label.lower()), None)
            return int(edge.current if edge else temps[key][0].current)

    return None


def read_fan_rpm(fan_index: int = 1) -> int | None:
    """Return fan RPM for fan *fan_index* (1 = CPU, 2 = GPU), or None."""
    fans = _sensors_fans()

    # alienware_wmi has labelled entries
    if "alienware_wmi" in fans:
        entries = fans["alienware_wmi"]
        if fan_index == 1:
            entry = next((f for f in entries if "cpu" in f.label.lower()), None)
            if entry is None and entries:
                entry = entries[0]
        else:
            entry = next((f for f in entries if "gpu" in f.label.lower()), None)
            if entry is None and len(entries) > 1:
                entry = entries[1]
        if entry is not None:
            return int(entry.current)

    # dell_ddv / dell_smm positional fallback
    for key in ("dell_ddv", "dell_smm"):
        if key in fans and len(fans[key]) >= fan_index:
            return int(fans[key][fan_index - 1].current)

    return None


# ── background worker ─────────────────────────────────────────────────────────

from PySide6.QtCore import QObject, QThread, Signal, Slot  # noqa: E402


class _SensorWorker(QObject):
    """Runs in a QThread; emits sensor data via signal (never blocks UI thread)."""

    data_ready = Signal(int, int, int, int)  # fan1_rpm, cpu_temp, fan2_rpm, gpu_temp

    @Slot()
    def read(self):
        fan1 = read_fan_rpm(1) or 0
        cpu  = read_cpu_temp()  or 0
        fan2 = read_fan_rpm(2) or 0
        gpu  = read_gpu_temp()  or 0
        self.data_ready.emit(fan1, cpu, fan2, gpu)


class SensorPoller(QObject):
    """
    Convenience wrapper: creates a QThread + worker, polls every *interval_ms*.
    Connect ``data_ready(fan1, cpu, fan2, gpu)`` to receive results on the
    main thread through Qt's queued connection (thread-safe, no manual locking).

    Usage::

        self._poller = SensorPoller(interval_ms=1000, parent=self.window)
        self._poller.data_ready.connect(self._update_sensor_ui)
        self._poller.start()
    """

    data_ready = Signal(int, int, int, int)

    def __init__(self, interval_ms: int = 1000, parent=None):
        super().__init__(parent)
        self._interval = interval_ms

        self._thread = QThread()
        self._worker = _SensorWorker()
        self._worker.moveToThread(self._thread)
        # Forward worker signal to our own (automatically queued cross-thread)
        self._worker.data_ready.connect(self.data_ready)

        self._timer = None   # created inside the thread

    def start(self):
        self._thread.started.connect(self._setup_timer)
        self._thread.start()

    @Slot()
    def _setup_timer(self):
        from PySide6.QtCore import QTimer as _QTimer
        self._timer = _QTimer()
        self._timer.setInterval(self._interval)
        self._timer.timeout.connect(self._worker.read)
        self._timer.start()
        # Read immediately on startup
        self._worker.read()

    def stop(self):
        if self._timer:
            self._timer.stop()
        self._thread.quit()
        self._thread.wait()
