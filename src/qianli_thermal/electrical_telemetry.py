# -*- coding: utf-8 -*-
"""Optional passive electrical telemetry (Hantek ESP32 UDP & UNI-T UT61E+ parser).
Telemetría eléctrica pasiva opcional (Hantek ESP32 UDP y parser UNI-T UT61E+).

Sanitized for public release: no hardcoded personal IPs or local machine paths.
Sanitizado para publicación: sin IPs personales ni rutas locales hardcodeadas.
"""
from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv4Address
from math import isfinite
import re
import socket
from time import perf_counter

HANTEK_REGISTERS: dict[str, tuple[int, float, float]] = {
    "hantek_v": (0x09, 0.01, 0.5),
    "hantek_ma": (0x0A, 1.0, 0.5),
    "hantek_output": (0x14, 1.0, 1.0),
}

UT_DC_UNITS: dict[str, tuple[str, float]] = {
    "DC Microamperios": ("uA", 0.001),
    "DC Miliamperios": ("mA", 1.0),
    "DC Amperios": ("A", 1000.0),
    "DC uA": ("uA", 0.001),
    "DC mA": ("mA", 1.0),
    "DC A": ("A", 1000.0),
}


@dataclass(frozen=True)
class TelemetryReading:
    status: str
    timestamp: float | None = None
    values: tuple = ()

    def is_fresh(self, now: float, max_age_s: float = 1.5) -> bool:
        return self.timestamp is not None and 0 <= now - self.timestamp <= max_age_s


class HantekUDPClient:
    """Read-only UDP client for ESP32-bridged Hantek power supplies on a local LAN."""

    def __init__(self, host: str, port: int) -> None:
        ip = IPv4Address(host)
        if not ip.is_private or ip.is_loopback or ip.is_unspecified:
            raise ValueError("Provide a valid local/private IPv4 address for the Hantek bridge.")
        self.target = (str(ip), int(port))

    def read_register(self, key: str, timeout: float = 0.5) -> TelemetryReading:
        reg, scale, _ = HANTEK_REGISTERS[key]
        start = perf_counter()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            sock.connect(self.target)
            sock.send(bytes((0xFF, 0xFF, 0x02, reg)))
            raw = sock.recv(32)
        if not re.fullmatch(rb"[0-9]{1,5}", raw) or int(raw) > 65535:
            raise ValueError("Invalid Hantek register response")
        val = int(raw)
        if key == "hantek_output" and val not in (0, 1):
            raise ValueError("Invalid output state")
        return TelemetryReading("Valid", (start + perf_counter()) / 2, (round(val * scale, 2),))


def parse_ut61e_dc_current(packet: dict) -> TelemetryReading:
    """Parse a UT61E+ DC current telemetry dictionary into mA."""
    if packet.get("st") != "CONECTADO":
        return TelemetryReading("No USB data")
    mode = UT_DC_UNITS.get(packet.get("fn", ""))
    if mode is None or mode[0] != packet.get("un"):
        return TelemetryReading("Select DC current on UT61E+")
    if packet.get("ex"):
        return TelemetryReading("Disable HOLD, REL, or Peak mode")
    try:
        value_ma = float(packet.get("vl", "")) * mode[1]
    except (TypeError, ValueError):
        return TelemetryReading("Out of range or no reading")
    if not isfinite(value_ma):
        return TelemetryReading("Out of range or no reading")
    return TelemetryReading("Valid", perf_counter(), (value_ma, packet["vl"], mode[0]))
