# -*- coding: utf-8 -*-
"""Local DLL discovery and SHA-256 integrity verification.
Detección local y verificación SHA-256 de DLLs originales.

Does NOT download, bundle, or modify third-party binaries.
NO descarga, empaqueta ni modifica binarios de terceros.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

EXPECTED_HASHES: dict[str, str] = {
    "libiruvc.dll": "b65158d4fe40bee411fac758c93462fd42804addb19642551b6cacd216a913ae",
    "libirisp.dll": "8c143e8fe5a58782e03e131c00b31311473d33759debdad7e5d1c1c3007d680e",
    "libircmd.dll": "de2f2e53dcd777a2c6aab911589e601aa6f55e5f24d865a067ff95e1eba34dba",
}


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file. / Calcula el SHA-256 de un archivo."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def discover_qianli_dir() -> Path:
    """Locate a user-supplied QianLi IR installation without modifying files.
    Localiza una instalación de QianLi IR del usuario sin modificar archivos.
    """
    candidates: list[Path] = []
    override = os.environ.get("QIANLI_IR_DIR", "").strip().strip('"')
    if override:
        candidates.append(Path(override))
    candidates.extend([
        Path(r"C:\QianLi IR"),
        Path(r"C:\Program Files\QianLi IR"),
        Path(r"C:\Program Files (x86)\QianLi IR"),
    ])
    for drive in "CDEFG":
        candidates.append(Path(f"{drive}:\\QianLi IR"))

    for candidate in candidates:
        if (candidate / "libiruvc.dll").is_file() and (candidate / "libircmd.dll").is_file():
            return candidate

    if override:
        raise FileNotFoundError(
            f"QIANLI_IR_DIR does not contain libiruvc.dll and libircmd.dll: {override}"
        )
    raise FileNotFoundError(
        "QianLi IR folder not found. Set QIANLI_IR_DIR to your local installation path."
    )


def verify_dll(name: str, base_dir: Path | None = None) -> Path:
    """Verify a DLL against its expected SHA-256 digest and return its path.
    Verifica una DLL contra su SHA-256 esperado y devuelve su ruta.
    """
    if name not in EXPECTED_HASHES:
        raise ValueError(f"Unsupported DLL name: {name}")
    directory = base_dir if base_dir is not None else discover_qianli_dir()
    target = directory / name
    if not target.is_file():
        raise FileNotFoundError(f"Missing {name} in {directory}")
    actual = sha256_file(target)
    expected = EXPECTED_HASHES[name]
    if actual != expected:
        raise RuntimeError(
            f"SHA-256 mismatch for {name}: got {actual}, expected {expected}"
        )
    return target


def register_dll_directory(directory: Path) -> object | None:
    """Register DLL search directory on Windows. / Registra directorio de DLLs en Windows."""
    if os.name == "nt" and directory.is_dir():
        return os.add_dll_directory(str(directory))
    return None
