# Mini_S_256Pro — USB/UVC & Radiometric Communication

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%20(64--bit)-3776AB.svg)](https://www.python.org/)
[![Ko-fi](https://img.shields.io/badge/Apoyar%20en-Ko--fi-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/1v14rk05)

> 🇬🇧 **Prefer English?** See [README.md](README.md) or [Architecture Documentation (EN)](docs/ARCHITECTURE_EN.md).

Módulos limpios de código abierto en Python para **comunicación USB/UVC, lectura de calibración SPI, manejo de fotogramas Y16/Y14 y conversión radiométrica** desarrollados específicamente para la cámara térmica **QianLi IR / MIIR `Mini_S_256Pro`** (`VID 0x0BDA : PID 0x5830`, `256×192`).

> ⚠️ **Aviso de Compatibilidad:** Este proyecto fue desarrollado y probado **exclusivamente con el modelo `Mini_S_256Pro`**. **No** se ha probado con ningún otro modelo de cámara térmica.

---

## 🎯 Alcance y Propósito

Este repositorio publica **únicamente los módulos esenciales de comunicación, contratos ABI y lecturas/conversiones** extraídos de una suite completa de I+D. Está diseñado para interoperabilidad de hardware, investigación y herramientas propias, **sin redistribuir software propietario, binarios ni datos personales**.

### Capacidades Principales
- **Detección Local e Integridad de DLLs** (`dll_manager.py`): Localiza la instalación local de `QianLi IR` en el equipo y valida sus hashes SHA-256 antes de cargarlas.
- **Contratos ABI de Solo Lectura SPI y SDK** (`spi_contracts.py`): Definiciones ABI de `libircmd.dll` para `spi_read`, `get_prop_tpd_params`, `get_tpd_calib_param` y `get_tpd_*_array` (`KT`, `BT`, `NUC-T`, `PARAM48` en rangos `LOW`/`HIGH`).
- **Guardia de Handle Seguro entre Hilos** (`command_guard.py`): Serializa la propiedad del handle (`RLock` + afinidad de hilo) para evitar reentradas concurrentes en USB/SDK.
- **Estructuras `ctypes` UVC / ISP y Worker Aislado** (`uvc_motor.py`): `DeviceInfo`, `VideoParameters`, `CallbackParameters`, `AGCParams`, `DetailParams`, `DDEParams` y búferes Y14 protegidos con centinelas (`0xFFFF`).
- **Matemática Radiométrica y Visual** (`radiometry.py`):
  - Conversión `Y16 -> Y14` (`>> 2`)
  - Mapeo lineal exacto `Y14 -> Y8` (`(y14 * 255) // 16383`)
  - Conversión `NUC-T` `uint16 -> °C` (`raw * 0.0625 - 273.15`)
  - Remapeo visual `uint8` con paridad exacta `IDIV`/`MOVSX` x86
- **Telemetría Eléctrica Opcional** (`electrical_telemetry.py`): Lectura pasiva UDP para fuentes Hantek vía ESP32 y multímetro UNI-T UT61E+ por USB (sin IPs ni rutas personales hardcodeadas).
- **Diagnóstico USB / UVC** (`tools/`): Detector PyUSB (`0x0BDA:0x5830`) y script PowerShell de solo lectura para modos UVC en Windows.

---

## 📁 Estructura del Repositorio

```text
Mini_S_256Pro-ThermalCam-Core/
├── README.md                  # Documentación en inglés
├── README.es.md               # Documentación en español (este archivo)
├── LICENSE                    # Licencia MIT (código Python original)
├── requirements.txt           # Dependencias mínimas de Python
├── .gitignore                 # Excluye DLLs, EXEs, logs, zips y datos locales
├── docs/
│   ├── ARCHITECTURE_EN.md     # Documentación técnica ABI y pipeline (EN)
│   ├── ARQUITECTURA_ES.md     # Documentación técnica ABI y pipeline (ES)
│   └── LEGAL_AND_PRIVACY.md   # Aviso legal, derechos de autor y privacidad (EN / ES)
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

## 🚀 Inicio Rápido (Windows x64)

1. **Instala Python 3.11+ (64 bits)** y las dependencias:
   ```powershell
   py -3.11 -m pip install -r requirements.txt
   ```
2. **Conserva tu instalación local de QianLi IR** (ej. `C:\QianLi IR`) con `libiruvc.dll`, `libircmd.dll` y `libirisp.dll`.
   - Opcionalmente define la variable de entorno:
     ```powershell
     $env:QIANLI_IR_DIR = "C:\QianLi IR"
     ```
3. **Verifica la cámara USB** (`VID 0x0BDA : PID 0x5830`):
   ```powershell
   python tools/check_camera_usb.py
   ```
4. **Inspecciona contratos ABI y utilidades matemáticas** (funciona en cualquier SO sin DLLs):
   ```powershell
   python tools/example_read_contracts.py
   ```

---

## 📌 Aviso / Notice

- **Sin binarios de terceros:** Este repositorio no incluye DLLs, EXEs, firmwares ni recursos OEM.
- Todo el código Python original se publica bajo **Licencia MIT** con fines de **interoperabilidad, investigación y diagnóstico**.
- Se entrega **"TAL CUAL"**, sin garantía. Consulta [docs/LEGAL_AND_PRIVACY.md](docs/LEGAL_AND_PRIVACY.md) para más detalles.

---

## ☕ Apoya el Proyecto / Support the Project

Si esta documentación, la investigación ABI o el código limpio de comunicación te ahorraron horas de trabajo o ayudaron en tu taller o proyecto, considera apoyar al autor con una donación:

👉 **Donar en Ko-fi:** **[https://ko-fi.com/1v14rk05](https://ko-fi.com/1v14rk05)**

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/1v14rk05)
