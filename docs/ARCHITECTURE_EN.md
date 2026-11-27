# Architecture & Protocol Reference (English)

## 1. Hardware & USB Identification
- **Target Device:** QianLi IR / MIIR (`Mini_S_256Pro`)
- **USB IDs:** `VID 0x0BDA` / `PID 0x5830`
- **Sensor Resolution:** `256 × 192` pixels (`49,152` pixels)
- **Raw Frame Format:** `Y16` (`98,304` bytes per frame, little-endian `uint16`), shifted right by 2 bits (`>> 2`) to obtain 14-bit `Y14` (`0..16383`).

---

## 2. Native Library Interface (User-Supplied Windows x64 DLLs)
The camera ecosystem relies on three native libraries from a local QianLi IR installation:

1. **`libiruvc.dll`** — UVC video stream & USB handle lifecycle:
   - `iruvc_create_handle()` → `void*`
   - `iruvc_camera_init(cam)` → `int`
   - `iruvc_camera_open_same(cam, &DeviceInfo(0x5830, 0x0BDA, None), 0)` → `int`
   - `iruvc_camera_stream_start(cam, &VideoParameters, &CallbackParameters)` → `int`
   - `iruvc_camera_stream_close(cam, idx)` / `iruvc_camera_close(cam)` / `iruvc_camera_release(cam)` / `iruvc_delete_handle(cam)`

2. **`libircmd.dll`** — Camera commands & SPI calibration reads:
   - `ircmd_create_handle(cam, 1)` / `ircmd_delete_handle(cmd)`
   - `get_prop_tpd_params(cmd, 5, &prop5)` / `set_prop_tpd_params(cmd, 5, val)` — Reads/switches temperature range (`0 = LOW/High-gain`, `1 = HIGH/Low-gain` depending on bank mapping).
   - `get_prop_auto_shutter_params` / `set_prop_auto_shutter_params` / `ooc_b_update` / `spi_config_save` — Shutter & NUC control.
   - `spi_read(cmd, addr, length, out_buf)` — Reads SPI flash in blocks (max internal block `256` B, safe max `65535` B).
   - `get_tpd_kt_array`, `get_tpd_bt_array`, `get_tpd_nuc_t_array`, `get_tpd_calib_param` — Decodes calibration tables.

3. **`libirisp.dll`** — Image & radiometric ISP stages:
   - Visual chain: `detail_extract_init/process` → `agc_init/process` → `dde_init/process` (with `0xFFFF` sentinel checks to catch silent native aborts).
   - Radiometric chain: `KTBT` → `ENV` → `nuc_t_init/process/destory`.

---

## 3. SPI Memory Map (`SDK_BY_PROP5`)

| Property 5 | `KT` (`0x962` B) | `BT` (`0x962` B) | `NUCT` (`0x4000` B) | `PARAM48` (`48` B) |
| :--- | :---: | :---: | :---: | :---: |
| **`0`** | `0xD1000` | `0xD2000` | `0xD3000` | `0xD7000` |
| **`1`** | `0xD8000` | `0xD9000` | `0xDA000` | `0xDE000` |

---

## 4. Radiometric & Visual Math
- **Y16 → Y14:** `y14 = y16 >> 2` (valid range `0..16383`).
- **Y14 → Y8 (Linear):** `y8 = (y14.astype(int32) * 255) // 16383` (matches `libirparse!y14_to_rgb` exact integer quotient).
- **NUC-T `uint16` → Celsius:** `T_C = raw * 0.0625 - 273.15`.
- **LUT Remapping (`uint8`):** Exact x86 `IDIV` truncation toward zero + `MOVSX` 16-bit sign extension before clipping to `0..255`.

---

**Support / Ko-fi:** [https://ko-fi.com/1v14rk05](https://ko-fi.com/1v14rk05)
