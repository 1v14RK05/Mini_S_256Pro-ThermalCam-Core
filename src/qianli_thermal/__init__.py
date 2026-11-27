# -*- coding: utf-8 -*-
"""QianLi ThermalCam Core — Essential USB/UVC, SPI & Radiometry Modules.
Módulos esenciales de comunicación USB/UVC, SPI y radiometría.
"""

from .command_guard import CommandOwner, InvalidCommandSession
from .radiometry import (
    CalibratedTable,
    nuct_to_celsius,
    nuct_word_to_celsius,
    remap_intensity_u8,
    y14_to_y8_linear,
    y16_to_y14,
)
from .spi_contracts import (
    DLL_SHA256 as IRCMD_DLL_SHA256,
    InvalidNativeRead,
    READ_RVAS,
    ReadResult,
    SDK_BY_PROP5,
    SIZE as SPI_TABLE_SIZES,
    get_spi_contract,
)

__all__ = [
    "CalibratedTable",
    "CommandOwner",
    "IRCMD_DLL_SHA256",
    "InvalidCommandSession",
    "InvalidNativeRead",
    "READ_RVAS",
    "ReadResult",
    "SDK_BY_PROP5",
    "SPI_TABLE_SIZES",
    "get_spi_contract",
    "nuct_to_celsius",
    "nuct_word_to_celsius",
    "remap_intensity_u8",
    "y14_to_y8_linear",
    "y16_to_y14",
]
