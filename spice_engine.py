"""ngspice-backed CE amplifier simulation engine.

This module is pure Python: it validates inputs, writes SPICE netlists, runs the
external ngspice executable and parses its output. It knows nothing about Flask.
All values inside the model are SI (V, ohm, F, Hz, s).
"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ANALYSES = ("dc", "ac", "tran")
MODEL_NAME = "LAB4NPN"
MODEL_LINE = ".model LAB4NPN NPN(IS=1E-14 BF=100 VAF=100)"
MAX_FREQ_HZ = 100_000.0

FIELDS = (
    "vcc", "r1", "r2", "rc", "re", "rl",
    "cin_f", "cout_f", "amplitude_v", "freq_hz",
)


class SpiceError(Exception):
    """Base class for every expected simulation failure."""


class InvalidInput(SpiceError):
    """Input is missing, non-numeric, non-finite or outside the allowed range."""


class NgspiceUnavailable(SpiceError):
    """The ngspice executable could not be found."""


class RunFailed(SpiceError):
    """ngspice exited with a non-zero status or timed out."""


class OutputEmpty(SpiceError):
    """ngspice produced no usable raw output."""


class ParseFailed(SpiceError):
    """The raw output could not be interpreted."""


@dataclass(frozen=True)
class SimInput:
    """Validated SI parameters for the reference CE voltage-divider circuit."""

    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    rl: float
    cin_f: float
    cout_f: float
    amplitude_v: float
    freq_hz: float

    def __post_init__(self) -> None:
        for name in FIELDS:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise InvalidInput(f"{name} must be a number")
            if not math.isfinite(value):
                raise InvalidInput(f"{name} must be finite")
            if value <= 0:
                raise InvalidInput(f"{name} must be greater than zero")
        if self.freq_hz > MAX_FREQ_HZ:
            raise InvalidInput(f"freq_hz must not exceed {MAX_FREQ_HZ:g}")


def _num(value: float) -> str:
    """Format a validated float for a SPICE deck (no user text is ever passed)."""
    return format(float(value), ".8g")


def build_netlist(params: SimInput, analysis: str) -> str:
    """Return a complete ngspice deck for the requested analysis."""
    if analysis not in ANALYSES:
        raise InvalidInput(f"Unknown analysis: {analysis}")

    period = 1.0 / params.freq_hz
    directives = {
        "dc": ".op",
        "ac": ".ac dec 20 10 10Meg",
        "tran": ".tran {step} {stop}".format(
            step=_num(period / 200.0), stop=_num(5.0 * period)
        ),
    }

    lines = [
        "* CE voltage divider reference - Lab 04",
        f"VCC vcc 0 {_num(params.vcc)}",
        f"VIC vcc rc_top 0",
        f"R1 vcc base {_num(params.r1)}",
        f"R2 base 0 {_num(params.r2)}",
        f"RC rc_top col {_num(params.rc)}",
        f"RE emi 0 {_num(params.re)}",
        f"RL out 0 {_num(params.rl)}",
        f"CIN in base {_num(params.cin_f)}",
        f"COUT col out {_num(params.cout_f)}",
        f"Q1 col base emi {MODEL_NAME}",
        "VS in 0 SIN(0 {amp} {freq}) AC 1".format(
            amp=_num(params.amplitude_v), freq=_num(params.freq_hz)
        ),
        MODEL_LINE,
        ".save v(in) v(out) v(base) v(emi) v(col) i(vic)",
        directives[analysis],
        ".end",
        "",
    ]
    return "\n".join(lines)


@dataclass(frozen=True)
class OpResult:
    vb: float
    ve: float
    vc: float
    vce: float
    ic: float


@dataclass(frozen=True)
class AcPoint:
    freq_hz: float
    gain_db: float
    gain_mag: float
    phase_deg: float


@dataclass(frozen=True)
class TranPoint:
    time_s: float
    vin_v: float
    vout_v: float


def _raw_columns(text: str) -> tuple[list[str], list[list[Any]]]:
    """Parse ngspice's ASCII raw format into named columns of numbers."""
    lines = text.splitlines()
    try:
        n_vars = int(next(line for line in lines
                          if line.startswith("No. Variables:")).split(":")[1])
        n_points = int(next(line for line in lines
                            if line.startswith("No. Points:")).split(":")[1])
        is_complex = any(line.startswith("Flags:") and "complex" in line
                         for line in lines)

        var_start = next(i for i, line in enumerate(lines)
                         if line.strip() == "Variables:") + 1
        names: list[str] = []
        for line in lines[var_start:]:
            parts = line.split()
            if len(parts) >= 2 and parts[0].isdigit():
                names.append(parts[1].lower())
                if len(names) == n_vars:
                    break
        if len(names) != n_vars:
            raise ParseFailed("raw file has fewer variables than declared")

        values_start = next(i for i, line in enumerate(lines)
                            if line.strip() == "Values:") + 1
        tokens: list[str] = []
        for line in lines[values_start:]:
            if not line.strip():
                continue
            parts = line.strip().split()
            # Every raw row starts with its own zero-based index.
            if len(parts) >= 2 and parts[0].isdigit():
                parts = parts[1:]
            tokens.extend(parts)
        expected = n_points * n_vars
        if n_points < 1 or len(tokens) < expected:
            raise ParseFailed("raw file has no data points")

        rows: list[list[Any]] = []
        for index in range(n_points):
            values = tokens[index * n_vars:(index + 1) * n_vars]
            row: list[Any] = []
            for value in values:
                if is_complex:
                    real, imag = value.split(",")
                    row.append(complex(float(real), float(imag)))
                else:
                    row.append(float(value))
            rows.append(row)
        return names, rows
    except (StopIteration, ValueError, IndexError) as exc:
        raise ParseFailed("could not read ngspice raw output") from exc


def _column(names: list[str], row: list[Any], name: str) -> Any:
    try:
        return row[names.index(name.lower())]
    except ValueError as exc:
        raise ParseFailed(f"raw file is missing {name}") from exc


def _as_float(value: complex | float) -> float:
    return float(value.real if isinstance(value, complex) else value)


def _db(value: complex | float) -> float:
    magnitude = abs(value)
    return 20.0 * math.log10(magnitude) if magnitude > 0 else -320.0


def _phase(value: complex | float) -> float:
    if isinstance(value, complex):
        return math.degrees(math.atan2(value.imag, value.real))
    return 0.0 if value >= 0 else 180.0


def _wrap(degrees: float) -> float:
    return (degrees + 180.0) % 360.0 - 180.0


def parse_op(raw_text: str) -> OpResult:
    names, rows = _raw_columns(raw_text)
    row = rows[0]
    vb = float(_column(names, row, "v(base)"))
    ve = float(_column(names, row, "v(emi)"))
    vc = float(_column(names, row, "v(col)"))
    ic = float(_column(names, row, "i(vic)"))
    return OpResult(vb=vb, ve=ve, vc=vc, vce=vc - ve, ic=ic)


def parse_ac(raw_text: str) -> list[AcPoint]:
    names, rows = _raw_columns(raw_text)
    points: list[AcPoint] = []
    for row in rows:
        freq = _as_float(_column(names, row, "frequency"))
        vin = _column(names, row, "v(in)")
        vout = _column(names, row, "v(out)")
        gain_db = _db(vout) - _db(vin)
        points.append(AcPoint(
            freq_hz=freq,
            gain_db=gain_db,
            gain_mag=10 ** (gain_db / 20.0),
            phase_deg=_wrap(_phase(vout) - _phase(vin)),
        ))
    return points


def parse_tran(raw_text: str) -> list[TranPoint]:
    names, rows = _raw_columns(raw_text)
    return [TranPoint(
        time_s=float(_column(names, row, "time")),
        vin_v=float(_column(names, row, "v(in)")),
        vout_v=float(_column(names, row, "v(out)")),
    ) for row in rows]


def find_cutoff(points: list[AcPoint]) -> float | None:
    """First downward -3 dB crossing relative to the passband maximum."""
    if len(points) < 3:
        return None
    threshold = max(point.gain_db for point in points) - 3.0
    in_passband = False
    for point in points:
        if point.gain_db > threshold:
            in_passband = True
        elif in_passband:
            return point.freq_hz
    return None


@dataclass(frozen=True)
class SimResult:
    analysis: str
    status: str
    model: str
    netlist: str
    log_excerpt: str
    version: str = "unknown"
    op: OpResult | None = None
    ac: list[AcPoint] = field(default_factory=list)
    tran: list[TranPoint] = field(default_factory=list)
    cutoff_hz: float | None = None
    warnings: list[str] = field(default_factory=list)


def find_ngspice() -> str | None:
    """Locate ngspice without hard-coding one machine's install path."""
    override = os.environ.get("NGSPICE_EXE")
    if override:
        return override if Path(override).exists() else None
    found = shutil.which("ngspice")
    if found:
        return found
    homes = [Path.home()]
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            homes.append(Path(local))
    for home in homes:
        roots = [home / "AppData" / "Local" / "Programs" / "ngspice",
                 home / "Programs" / "ngspice"]
        for root in roots:
            if root.is_dir():
                for exe in root.rglob("ngspice.exe"):
                    return str(exe)
    return None


def _version_from_raw(raw_text: str) -> str:
    for line in raw_text.splitlines():
        if line.startswith("Command:"):
            return line.split(":", 1)[1].strip()
    return "unknown"


def _run_once(params: SimInput, analysis: str, exe: str, timeout: float):
    """Write a deck, run ngspice in batch mode and return (netlist, log, raw)."""
    netlist = build_netlist(params, analysis)
    with tempfile.TemporaryDirectory(prefix="lab04-spice-") as workdir:
        directory = Path(workdir)
        deck = directory / "ce.cir"
        log_path = directory / "ce.log"
        raw_path = directory / "ce.raw"
        deck.write_text(netlist, encoding="utf-8")

        command = [exe, "-b", "-o", str(log_path), "-r", str(raw_path), str(deck)]
        try:
            process = subprocess.run(
                command,
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RunFailed(f"ngspice timed out after {timeout:g} s") from exc
        except OSError as exc:
            raise NgspiceUnavailable(f"could not start ngspice: {exc}") from exc

        if process.returncode != 0:
            detail = (process.stderr or process.stdout or "").strip()[:400]
            raise RunFailed(f"ngspice exited with status {process.returncode}: {detail}")

        if not raw_path.exists() or raw_path.stat().st_size == 0:
            raise OutputEmpty("ngspice produced no raw output")
        raw_text = raw_path.read_text(encoding="utf-8", errors="replace")
        if not raw_text.strip():
            raise OutputEmpty("ngspice raw output is empty")
        log_text = (log_path.read_text(encoding="utf-8", errors="replace")
                    if log_path.exists() else "")
        return netlist, log_text, raw_text


def run_analysis(params: SimInput, analysis: str, *, exe: str | None = None,
                 timeout: float = 30.0) -> SimResult:
    """Run one real ngspice analysis and return parsed, provenance-tagged data."""
    if analysis not in ANALYSES:
        raise InvalidInput(f"Unknown analysis: {analysis}")
    engine = exe or find_ngspice()
    if not engine or not Path(engine).exists():
        raise NgspiceUnavailable(
            "ngspice not found — install it or set NGSPICE_EXE to ngspice.exe"
        )

    netlist, log_text, raw_text = _run_once(params, analysis, engine, timeout)
    op = None
    ac: list[AcPoint] = []
    tran: list[TranPoint] = []
    cutoff: float | None = None
    try:
        if analysis == "dc":
            op = parse_op(raw_text)
        elif analysis == "ac":
            ac = parse_ac(raw_text)
            cutoff = find_cutoff(ac)
        else:
            tran = parse_tran(raw_text)
    except ParseFailed:
        raise
    except (ValueError, IndexError, KeyError, ZeroDivisionError) as exc:
        raise ParseFailed(f"could not interpret ngspice results: {exc}") from exc

    warnings = [line.strip() for line in log_text.splitlines()
                if "warning" in line.lower()][:10]
    return SimResult(
        analysis=analysis,
        status="success",
        model=MODEL_NAME,
        netlist=netlist,
        log_excerpt=log_text[:4000],
        version=_version_from_raw(raw_text),
        op=op,
        ac=ac,
        tran=tran,
        cutoff_hz=cutoff,
        warnings=warnings,
    )


def ngspice_version(exe: str | None = None) -> str:
    """Return the version string printed by ngspice in a real batch run."""
    engine = exe or find_ngspice()
    if not engine or not Path(engine).exists():
        raise NgspiceUnavailable("ngspice not found")
    _, _, raw_text = _run_once(
        SimInput(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0, re=1_000.0,
                 rl=10_000.0, cin_f=10e-6, cout_f=10e-6,
                 amplitude_v=0.010, freq_hz=1_000.0),
        "dc", engine, 30.0,
    )
    return _version_from_raw(raw_text)
