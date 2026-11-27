# QianLi ThermalCam Core — USB/UVC & Radiometric Communication

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%20(64--bit)-3776AB.svg)](https://www.python.org/)
[![Ko-fi](https://img.shields.io/badge/Support%20on-Ko--fi-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/1v14rk05)

> 🇪🇸 **¿Prefieres leer en español?** Consulta [README.es.md](README.es.md) o la [Documentación de Arquitectura (ES)](docs/ARQUITECTURA_ES.md).

Clean, open-source Python modules for **USB/UVC communication, SPI calibration reading, Y16/Y14 frame handling, and radiometric conversion** with **QianLi IR / MIIR (`Mini_S_256Pro`)** thermal cameras (`VID 0x0BDA : PID 0x5830`, `256×192`).

---

## 🎯 Scope & Purpose

This repository publishes **only the essential communication, ABI contracts, and reading/conversion modules** extracted from a larger R&D suite. It is designed for hardware interoperability, research, and custom tooling without redistributing any proprietary software, binaries, or personal data.

### Key Capabilities
- **Local DLL Discovery & Integrity Verification** (`dll_manager.py`): Locates a local `QianLi IR` installation and verifies SHA-256 digests before loading.
- **Read-Only SPI & SDK ABI Contracts** (`spi_contracts.py`): `libircmd.dll` ABI definitions for `spi_read`, `get_prop_tpd_params`, `get_tpd_calib_param`, and `get_tpd_*_array` (`KT`, `BT`, `NUC-T`, `PARAM48` across `LOW`/`HIGH` ranges).
- **Thread-Safe Command Handle Guard** (`command_guard.py`): Serializes handle ownership (`RLock` + thread affinity) to prevent concurrent SDK/USB re-entrancy.
- **UVC / ISP `ctypes` Structures & Isolated Worker** (`uvc_motor.py`): `DeviceInfo`, `VideoParameters`, `CallbackParameters`, `AGCParams`, `DetailParams`, `DDEParams`, and sentinel-guarded Y14 buffers (`0xFFFF` canary checks).
- **Radiometric & Visual Math** (`radiometry.py`):
  - `Y16 -> Y14` bit-shift (`>> 2`)
  - Exact `Y14 -> Y8` linear mapping (`(y14 * 255) // 16383`)
  - `NUC-T` `uint16 -> °C` conversion (`raw * 0.0625 - 273.15`)
  - `uint8` LUT remapping with x86 `IDIV`/`MOVSX` parity
- **Optional Electrical Telemetry** (`electrical_telemetry.py`): Passive UDP reader for ESP32-bridged Hantek power supplies and UNI-T UT61E+ USB multimeter parser (no hardcoded IPs or local paths).
- **USB / UVC Diagnostics** (`tools/`): Standalone PyUSB device detector (`0x0BDA:0x5830`) and read-only Windows UVC PowerShell diagnostic.

---

## 📁 Repository Structure

```text
QianLi-ThermalCam-Core/
├── README.md                  # English documentation (this file)
├── README.es.md               # Documentación completa en español
├── LICENSE                    # MIT License (original Python code)
├── requirements.txt           # Minimal Python dependencies
├── .gitignore                 # Excludes DLLs, EXEs, logs, zips, and local data
├── docs/
│   ├── ARCHITECTURE_EN.md     # Technical ABI & pipeline documentation (EN)
│   ├── ARQUITECTURA_ES.md     # Documentación técnica ABI y pipeline (ES)
│   └── LEGAL_AND_PRIVACY.md   # Legal, copyright & privacy notice (EN / ES)
├── src/
│   └── qianli_thermal/
│       ├── __init__.py
│       ├── dll_manager.py
│       ├── spi_contracts.py
│       ├── command_guard.py
│       ├── uvc_motor.py
│       ├── radiometry.py
│       └── electrical_telemetry.py
└── tools/
    ├── check_camera_usb.py
    ├── diagnostico_uvc_windows.ps1
    └── example_read_contracts.py
```

---

## 🚀 Quick Start (Windows x64)

1. **Install Python 3.11+ (64-bit)** and install dependencies:
   ```powershell
   py -3.11 -m pip install -r requirements.txt
   ```
2. **Ensure you have a local installation of QianLi IR** (e.g., `C:\QianLi IR`) containing `libiruvc.dll`, `libircmd.dll`, and `libirisp.dll`.
   - Optionally set the environment variable:
     ```powershell
     $env:QIANLI_IR_DIR = "C:\QianLi IR"
     ```
3. **Check USB camera presence** (`VID 0x0BDA : PID 0x5830`):
   ```powershell
   python tools/check_camera_usb.py
   ```
4. **Inspect ABI contracts & math utilities** (works on any OS without DLLs):
   ```powershell
   python tools/example_read_contracts.py
   ```

---

## 📌 Notice / Aviso

- **No third-party binaries included:** This repository contains no DLLs, EXEs, firmware images, or OEM assets.
- All original Python code is licensed under the **MIT License** for **interoperability, research, and diagnostic purposes**.
- Provided **"AS IS"** without warranty. See [docs/LEGAL_AND_PRIVACY.md](docs/LEGAL_AND_PRIVACY.md) for details.

---

## ☕ Support the Project / Apoya el Proyecto

If this documentation, ABI research, or clean communication code saved you hours of reverse engineering or helped your repair/diagnostic workflow, consider supporting the author:

👉 **Donate on Ko-fi:** **[https://ko-fi.com/1v14rk05](https://ko-fi.com/1v14rk05)**

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/1v14rk05)
