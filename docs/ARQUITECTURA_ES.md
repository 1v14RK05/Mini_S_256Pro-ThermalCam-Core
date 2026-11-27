# Referencia de Arquitectura y Protocolo (Español)

## 1. Identificación de Hardware y USB
- **Dispositivo objetivo:** QianLi IR / MIIR (`Mini_S_256Pro`)
- **IDs USB:** `VID 0x0BDA` / `PID 0x5830`
- **Resolución del sensor:** `256 × 192` píxeles (`49,152` píxeles)
- **Formato de fotograma crudo:** `Y16` (`98,304` bytes por fotograma, `uint16` little-endian), desplazado 2 bits a la derecha (`>> 2`) para obtener `Y14` de 14 bits (`0..16383`).

---

## 2. Interfaz con Bibliotecas Nativas (DLLs locales en Windows x64)
El ecosistema de la cámara utiliza tres bibliotecas nativas de una instalación local de QianLi IR:

1. **`libiruvc.dll`** — Ciclo de vida USB y flujo de vídeo UVC:
   - `iruvc_create_handle()` → `void*`
   - `iruvc_camera_init(cam)` → `int`
   - `iruvc_camera_open_same(cam, &DeviceInfo(0x5830, 0x0BDA, None), 0)` → `int`
   - `iruvc_camera_stream_start(cam, &VideoParameters, &CallbackParameters)` → `int`
   - `iruvc_camera_stream_close(cam, idx)` / `iruvc_camera_close(cam)` / `iruvc_camera_release(cam)` / `iruvc_delete_handle(cam)`

2. **`libircmd.dll`** — Comandos de cámara y lecturas de calibración SPI:
   - `ircmd_create_handle(cam, 1)` / `ircmd_delete_handle(cmd)`
   - `get_prop_tpd_params(cmd, 5, &prop5)` / `set_prop_tpd_params(cmd, 5, val)` — Lee/cambia el rango de temperatura (`0` / `1` según el banco).
   - `get_prop_auto_shutter_params` / `set_prop_auto_shutter_params` / `ooc_b_update` / `spi_config_save` — Control de obturador y NUC.
   - `spi_read(cmd, addr, length, out_buf)` — Lee la memoria SPI por bloques (bloque interno máximo `256` B, máximo seguro `65535` B).
   - `get_tpd_kt_array`, `get_tpd_bt_array`, `get_tpd_nuc_t_array`, `get_tpd_calib_param` — Decodifica tablas de calibración.

3. **`libirisp.dll`** — Etapas ISP visuales y radiométricas:
   - Cadena visual: `detail_extract_init/process` → `agc_init/process` → `dde_init/process` (con centinelas `0xFFFF` para detectar abortos silenciosos).
   - Cadena radiométrica: `KTBT` → `ENV` → `nuc_t_init/process/destory`.

---

## 3. Mapa de Memoria SPI (`SDK_BY_PROP5`)

| Propiedad 5 | `KT` (`0x962` B) | `BT` (`0x962` B) | `NUCT` (`0x4000` B) | `PARAM48` (`48` B) |
| :--- | :---: | :---: | :---: | :---: |
| **`0`** | `0xD1000` | `0xD2000` | `0xD3000` | `0xD7000` |
| **`1`** | `0xD8000` | `0xD9000` | `0xDA000` | `0xDE000` |

---

## 4. Matemática Radiométrica y Visual
- **Y16 → Y14:** `y14 = y16 >> 2` (rango válido `0..16383`).
- **Y14 → Y8 (Lineal):** `y8 = (y14.astype(int32) * 255) // 16383` (coincide exactamente con el cociente entero de `libirparse!y14_to_rgb`).
- **NUC-T `uint16` → Celsius:** `T_C = raw * 0.0625 - 273.15`.
- **Remapeo LUT (`uint8`):** Emulación exacta del truncado hacia cero de `IDIV` x86 + extensión de signo `MOVSX` de 16 bits antes de recortar a `0..255`.

---

**Apoyo / Ko-fi:** [https://ko-fi.com/1v14rk05](https://ko-fi.com/1v14rk05)
