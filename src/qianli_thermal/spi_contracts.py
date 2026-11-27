# -*- coding: utf-8 -*-
"""Read-only ABI contracts for libircmd.dll (SPI & TPD calibration reads).
Contratos ABI de solo lectura para libircmd.dll (lecturas SPI y calibración TPD).

Importing this module does NOT load any DLL, open USB, or execute commands.
Importar este módulo NO carga DLLs, no abre USB ni ejecuta comandos.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

DLL_SHA256 = "de2f2e53dcd777a2c6aab911589e601aa6f55e5f24d865a067ff95e1eba34dba"

READ_RVAS: dict[str, int] = {
    "spi_read": 0x3CB0,
    "get_prop_tpd_params": 0x19E0,
    "get_tpd_calib_param": 0x1C60,
    "get_tpd_kt_array": 0x1DC0,
    "get_tpd_bt_array": 0x1B20,
    "get_tpd_nuc_t_array": 0x1F00,
}

SIZE: dict[str, int] = {
    "KT": 0x962,    # 2,402 bytes
    "BT": 0x962,    # 2,402 bytes
    "NUCT": 0x4000, # 16,384 bytes (8,192 uint16 entries)
}

SDK_BY_PROP5: dict[int, dict[str, int]] = {
    0: {"KT": 0xD1000, "BT": 0xD2000, "NUCT": 0xD3000, "PARAM48": 0xD7000},
    1: {"KT": 0xD8000, "BT": 0xD9000, "NUCT": 0xDA000, "PARAM48": 0xDE000},
}


class InvalidNativeRead(ValueError):
    """Raised when a native SPI/SDK read fails validation."""


@dataclass(frozen=True)
class ReadResult:
    """Validated read-only SPI/TPD table buffer. / Búfer validado de tabla SPI/TPD."""

    kind: str
    content: bytes
    native_code: int
    prop5_initial: int
    prop5_final: int
    source: str = "get_tpd_*_array"

    def __post_init__(self) -> None:
        if self.kind not in SIZE:
            raise InvalidNativeRead(f"Unsupported table kind: {self.kind}")
        if self.native_code != 0:
            raise InvalidNativeRead(f"SDK returned error code {self.native_code}; data discarded")
        if self.prop5_initial not in SDK_BY_PROP5 or self.prop5_final != self.prop5_initial:
            raise InvalidNativeRead("Property 5 changed or is ambiguous during read")
        if not isinstance(self.content, bytes) or len(self.content) != SIZE[self.kind]:
            raise InvalidNativeRead("Incompatible output buffer length")
        if self.content == self.content[:2] * (len(self.content) // 2):
            raise InvalidNativeRead("Uniform/empty table rejected")

    def manifest(self) -> dict:
        """Return a safe metadata summary (no raw sensor bytes)."""
        return {
            "kind": self.kind,
            "buffer_size": len(self.content),
            "sdk_status": self.native_code,
            "prop5": self.prop5_initial,
            "spi_address": hex(SDK_BY_PROP5[self.prop5_initial][self.kind]),
            "sha256": sha256(self.content).hexdigest(),
        }


def get_spi_contract() -> dict:
    """Return documented Windows x64 ABI specifications for libircmd.dll."""
    return {
        "spi_read": {
            "abi": "Windows x64 (RCX, RDX, R8, R9)",
            "args": ["cmd_handle", "spi_addr:uint32", "length:uint16", "out_ptr"],
            "return": "int32 (0 = success, negative = error; NOT byte count)",
            "max_internal_block": 256,
            "max_safe_length": 65535,
            "operation": "read-only (never calls set_tpd or spi_config_save)",
        },
        "get_prop_tpd_params": {
            "args": ["cmd_handle", "selector:int32", "out:uint32*"],
            "range_property": 5,
            "note": "Writes 32-bit int; SDK compares low word against 0",
        },
        "get_tpd_*_array": {
            "args": ["cmd_handle", "out_ptr"],
            "return": "int32 (0 = internal loop finished; does not return byte count)",
            "sizes": SIZE,
            "internal_swap16": True,
            "warning": "May copy temp buffer even if spi_read fails; discard on non-zero return",
        },
        "get_tpd_calib_param": {
            "args": ["cmd_handle", "out:uint16[3]"],
            "output_bytes": 6,
            "spi_source_bytes": 48,
            "note": "Reads 48 B and exposes first 3 uint16 values decoded as BIG ENDIAN",
        },
    }
