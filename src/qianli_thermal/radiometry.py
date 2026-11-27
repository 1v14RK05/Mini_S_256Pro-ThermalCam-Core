# -*- coding: utf-8 -*-
"""Radiometric & visual conversion utilities for QianLi 256x192 thermal frames.
Utilidades de conversión radiométrica y visual para fotogramas térmicos QianLi 256x192.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import numpy as np

TABLE_U16 = 8192


def y16_to_y14(raw_y16: bytes, invert: bool = False) -> bytes | None:
    """Convert raw little-endian Y16 buffer to 14-bit Y14 (>> 2).
    Convierte un búfer Y16 little-endian a Y14 de 14 bits (>> 2).
    """
    y16 = np.frombuffer(raw_y16, dtype="<u2")
    if (int(y16.min()) >> 2) == (int(y16.max()) >> 2):
        return None
    y14 = np.right_shift(y16, 2)
    if invert:
        y14 = np.uint16(16383) - y14
    return y14.astype("<u2", copy=False).tobytes()


def y14_to_y8_linear(y14_array: np.ndarray) -> np.ndarray:
    """Exact Y14 -> Y8 linear mapping matching libirparse!y14_to_rgb: floor(y14 * 255 / 16383).
    Mapeo lineal exacto Y14 -> Y8 equivalente a libirparse!y14_to_rgb.
    """
    arr = np.asarray(y14_array)
    if arr.dtype != np.uint16:
        raise TypeError("Expected uint16 Y14 array")
    if arr.ndim != 2:
        raise ValueError("Expected 2D Y14 array")
    if arr.size and int(arr.max()) > 16383:
        raise ValueError("Y14 values must be within 0..16383")
    return ((arr.astype(np.int32) * 255) // 16383).astype(np.uint8)


def nuct_to_celsius(raw_nuct: np.ndarray) -> np.ndarray:
    """Convert NUC-T uint16 values to degrees Celsius: raw * 0.0625 - 273.15.
    Convierte valores uint16 NUC-T a grados Celsius: raw * 0.0625 - 273.15.
    """
    return (np.asarray(raw_nuct, dtype=np.float64) * 0.0625 - 273.15).astype(np.float32)


def nuct_word_to_celsius(raw: int) -> float:
    """Convert a single NUC-T uint16 word to degrees Celsius."""
    if type(raw) is not int or not 0 <= raw <= 65535:
        raise ValueError("Expected uint16 NUC-T word (0..65535)")
    return float(np.float32(raw * 0.0625 - 273.15))


def remap_intensity_u8(intensity_u8: np.ndarray, low: int = 0, high: int = 255) -> np.ndarray:
    """Remap uint8 intensity to LUT index with exact x86 IDIV truncation & MOVSX parity.
    Remapea intensidad uint8 a índice de LUT con paridad exacta IDIV/MOVSX x86.
    """
    arr = np.asarray(intensity_u8)
    if arr.dtype != np.uint8:
        raise TypeError("Expected uint8 image")
    low, high = int(low), int(high)
    if not 0 <= low < high <= 255:
        raise ValueError("Invalid range: require 0 <= low < high <= 255")
    num = (arr.astype(np.int32) - low) * 255
    den = high - low
    q = np.where(num >= 0, num // den, -((-num) // den))
    q16 = ((q + 32768) & 0xFFFF) - 32768
    return np.clip(q16, 0, 255).astype(np.uint8)


@dataclass(frozen=True)
class CalibratedTable:
    """Validated 8192-word (16 KB) NUC-T calibration table."""

    data: bytes
    digest: str
    source: str
    range_mode: str

    @classmethod
    def from_bytes(cls, data: bytes, source: str, range_mode: str) -> "CalibratedTable":
        if range_mode not in ("LOW", "HIGH"):
            raise ValueError("range_mode must be 'LOW' or 'HIGH'")
        if not isinstance(data, bytes) or len(data) != TABLE_U16 * 2:
            raise ValueError(f"Expected {TABLE_U16 * 2} bytes for NUC-T table")
        arr = np.frombuffer(data, dtype="<u2")
        if np.all(arr == arr[0]):
            raise ValueError("Calibration table is uniform/unusable")
        return cls(bytes(data), sha256(data).hexdigest(), str(source), range_mode)

    @classmethod
    def from_file(cls, path: str | Path, range_mode: str) -> "CalibratedTable":
        p = Path(path).resolve(strict=True)
        return cls.from_bytes(p.read_bytes(), str(p), range_mode)
