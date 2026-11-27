# -*- coding: utf-8 -*-
"""UVC & ISP ctypes ABI structures and sentinel-guarded Y14/Y16 buffers.
Estructuras ABI ctypes para UVC/ISP y búferes Y14/Y16 protegidos con centinelas.

Requires a user-supplied Windows x64 QianLi IR installation to execute native ISP calls.
Requiere una instalación local en Windows x64 de QianLi IR para ejecutar llamadas ISP nativas.
"""
from __future__ import annotations

import ctypes as C
import os
from pathlib import Path
import numpy as np

from .dll_manager import register_dll_directory, verify_dll

WIDTH, HEIGHT = 256, 192
PIXELS = WIDTH * HEIGHT
FRAME_BYTES = PIXELS * 2
VID_QIANLI = 0x0BDA
PID_MINI_S_256PRO = 0x5830


def validate_y14(data: bytes) -> bytes:
    """Validate 256x192 Y14 frame bytes (each uint16 <= 16383)."""
    if not isinstance(data, bytes) or len(data) != FRAME_BYTES:
        raise ValueError(f"Invalid Y14 length: expected {FRAME_BYTES} bytes")
    if int(np.frombuffer(data, dtype="<u2").max()) > 16383:
        raise ValueError("Y14 sample out of range (> 16383)")
    return data


class DeviceInfo(C.Structure):
    _fields_ = [
        ("pid", C.c_uint32),
        ("vid", C.c_uint32),
        ("identifier", C.c_void_p),
    ]


class VideoParameters(C.Structure):
    _fields_ = [
        ("device", DeviceInfo),
        ("format", C.c_char_p),
        ("width", C.c_uint32),
        ("height", C.c_uint32),
        ("frame_size", C.c_uint32),
        ("fps", C.c_uint32),
        ("timeout", C.c_uint32),
        ("reserved", C.c_uint32),
    ]


FrameCallback = C.CFUNCTYPE(None, C.c_void_p, C.c_void_p)


class CallbackParameters(C.Structure):
    _fields_ = [
        ("camera", C.c_void_p),
        ("callback", FrameCallback),
        ("userdata", C.c_void_p),
    ]


class ISPContext(C.Structure):
    _fields_ = [
        ("mode", C.c_int32),
        ("_pad", C.c_int32),
        ("params", C.c_void_p),
        ("descriptor", C.c_void_p),
        ("input", C.c_void_p),
        ("output", C.c_void_p),
        ("callback", C.c_void_p),
        ("userdata", C.c_void_p),
    ]


class ISPDescriptor(C.Structure):
    _pack_ = 1
    _fields_ = [
        ("_00", C.c_uint8 * 2),
        ("width", C.c_uint16),
        ("height", C.c_uint16),
        ("bpp", C.c_uint16),
        ("_08", C.c_uint8 * 56),
        ("agc_aux", C.c_void_p),
        ("detail_aux", C.c_void_p),
    ]


class AGCParams(C.Structure):
    _fields_ = [
        ("f0", C.c_float),
        ("f1", C.c_float),
        ("f2", C.c_float),
        ("f3", C.c_float),
        ("i4", C.c_int32),
        ("f5", C.c_float),
        ("f6", C.c_float),
        ("i7", C.c_int32),
    ]


class DetailParams(C.Structure):
    _fields_ = [("radius", C.c_int32), ("strength", C.c_float)]


class DDEParams(C.Structure):
    _fields_ = [
        ("f0", C.c_float),
        ("f1", C.c_float),
        ("f2", C.c_float),
        ("i3", C.c_int32),
        ("i4", C.c_int32),
        ("i5", C.c_int32),
        ("i6", C.c_int32),
    ]


assert C.sizeof(ISPContext) == 56 and C.sizeof(ISPDescriptor) == 80


class GuardedBuffer:
    """Memory buffer surrounded by canary bytes to detect out-of-bounds native writes."""

    def __init__(self, size: int = FRAME_BYTES, marker: int = 0xC5, pad: int = 4096) -> None:
        self.size = size
        self.marker = marker
        self.pad = pad
        self.mem = (C.c_ubyte * (size + 2 * pad))()
        C.memset(C.addressof(self.mem), marker, len(self.mem))
        self.ptr = C.addressof(self.mem) + pad

    def write(self, content: bytes) -> None:
        if len(content) != self.size:
            raise ValueError(f"Expected {self.size} bytes, got {len(content)}")
        C.memmove(self.ptr, content, self.size)

    def read(self) -> bytes:
        return C.string_at(self.ptr, self.size)

    def guards_intact(self) -> bool:
        expected = bytes([self.marker]) * self.pad
        return bytes(self.mem[: self.pad]) == expected and bytes(self.mem[-self.pad :]) == expected


class NativeISPSession:
    """Isolated Detail -> AGC -> DDE session over user-supplied libirisp.dll (Windows x64)."""

    def __init__(self, qianli_dir: Path | None = None) -> None:
        if os.name != "nt" or C.sizeof(C.c_void_p) != 8:
            raise RuntimeError("NativeISPSession requires Windows x64")
        dll_path = verify_dll("libirisp.dll", qianli_dir)
        self._dll_dir_handle = register_dll_directory(dll_path.parent)
        self.dll = C.WinDLL(str(dll_path))

        for func in ("agc_init", "dde_init", "detail_extract_init"):
            fn = getattr(self.dll, func)
            fn.argtypes = [C.c_void_p, C.c_int32] + [C.c_void_p] * 6
            fn.restype = C.c_int32
        for func in ("agc_process", "dde_process", "detail_extract_process"):
            fn = getattr(self.dll, func)
            fn.argtypes = [C.c_void_p]
            fn.restype = C.c_int32

        self.source = GuardedBuffer(marker=0xA7)
        self.agc = GuardedBuffer(marker=0xB9)
        self.detail = GuardedBuffer(marker=0xC7)
        self.dde = GuardedBuffer(marker=0xD9)
        self.aux_agc = (C.c_ubyte * 67336)()

        self.desc = ISPDescriptor()
        self.desc.width, self.desc.height, self.desc.bpp = WIDTH, HEIGHT, 2
        self.desc.agc_aux = C.addressof(self.aux_agc)
        self.desc.detail_aux = self.detail.ptr

        self.agc_params = AGCParams(0.000025, 0.00003, 0.0001, 0.0001, 150, 0.8, 0.25, 5)
        self.detail_params = DetailParams(3, 1.0)
        self.dde_params = DDEParams(0.0, 96.0, 48.0, 0, 10, 30, 100)

    def _invoke(self, prefix: str, mode: int, params: C.Structure, inp: GuardedBuffer, out: GuardedBuffer) -> None:
        ctx = ISPContext()
        rc = getattr(self.dll, f"{prefix}_init")(
            C.byref(ctx), mode, C.byref(params), C.byref(self.desc),
            C.c_void_p(inp.ptr), C.c_void_p(out.ptr), None, None,
        )
        if rc != 0 or ctx.input != inp.ptr or ctx.output != out.ptr:
            raise RuntimeError(f"{prefix}_init failed: rc={rc}")
        rc = getattr(self.dll, f"{prefix}_process")(C.byref(ctx))
        if rc != 0:
            raise RuntimeError(f"{prefix}_process failed: rc={rc}")

    def process(self, y14: bytes, mode: str = "agc_dde") -> bytes:
        """Run Detail -> AGC -> DDE on a valid Y14 frame with 0xFFFF sentinel verification."""
        validate_y14(y14)
        if mode == "original":
            return y14
        self.source.write(y14)
        self._invoke("detail_extract", 0, self.detail_params, self.source, self.detail)

        C.memset(self.agc.ptr, 0xFF, FRAME_BYTES)
        self._invoke("agc", 1, self.agc_params, self.source, self.agc)
        agc_out = self.agc.read()
        if np.any(np.frombuffer(agc_out, dtype="<u2") == 0xFFFF):
            raise RuntimeError("Incomplete AGC output (sentinel 0xFFFF untouched)")
        validate_y14(agc_out)
        if mode == "agc":
            return agc_out

        C.memset(self.dde.ptr, 0xFF, FRAME_BYTES)
        self._invoke("dde", 0, self.dde_params, self.agc, self.dde)
        dde_out = self.dde.read()
        if np.any(np.frombuffer(dde_out, dtype="<u2") == 0xFFFF):
            raise RuntimeError("Incomplete DDE output (sentinel 0xFFFF untouched)")
        return validate_y14(dde_out)
