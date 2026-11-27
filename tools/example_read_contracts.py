# -*- coding: utf-8 -*-
"""Example: Inspect SPI contracts and radiometric conversions without hardware or DLLs.
Ejemplo: Inspeccionar contratos SPI y conversiones radiométricas sin hardware ni DLLs.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qianli_thermal import (
    CommandOwner,
    get_spi_contract,
    nuct_word_to_celsius,
    remap_intensity_u8,
    y14_to_y8_linear,
)


def main() -> None:
    print("=== SPI / SDK Read-Only Contracts ===")
    print(json.dumps(get_spi_contract(), indent=2))

    print("\n=== Radiometry & Visual Math Smoke Check ===")
    sample_y14 = np.array([[0, 8191], [12287, 16383]], dtype=np.uint16)
    y8 = y14_to_y8_linear(sample_y14)
    print("Y14 -> Y8:", y8.tolist())
    print("Remap (low=32, high=220):", remap_intensity_u8(y8, low=32, high=220).tolist())
    print("NUC-T 4800 -> Celsius:", round(nuct_word_to_celsius(4800), 2), "°C")

    guard = CommandOwner()
    print("CommandOwner initial state:", guard.summary())


if __name__ == "__main__":
    main()
