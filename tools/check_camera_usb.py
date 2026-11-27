# -*- coding: utf-8 -*-
"""Check USB presence and iProduct descriptor for QianLi ThermalCam (0x0BDA:0x5830).
Verifica la presencia USB y descriptor iProduct de la cámara térmica QianLi (0x0BDA:0x5830).
"""
import usb.core
import usb.util

VID = 0x0BDA
PID = 0x5830


def main() -> int:
    dev = usb.core.find(idVendor=VID, idProduct=PID)
    if dev is None:
        print(f"Error: USB device {VID:04x}:{PID:04x} not found.")
        return 1

    print(f"Device found / Dispositivo encontrado: {dev}")
    try:
        iproduct = usb.util.get_string(dev, dev.iProduct)
        print(f"iProduct: {iproduct}")
    except Exception as exc:
        print(f"Could not read iProduct (driver may be bound to UVC/WinUSB): {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
