# Read-only Windows UVC & PnP diagnostic for QianLi ThermalCam (VID_0BDA&PID_5830 / 5840).
# Does NOT open the video stream, send USB controls, or alter drivers.
$ErrorActionPreference = 'Continue'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$out = Join-Path (Get-Location) "Diagnostico_Modos_UVC_$stamp"
New-Item -ItemType Directory -Path $out -Force | Out-Null
$log = Join-Path $out 'debug.log'

function Log($s) {
    $line = "$(Get-Date -Format o) $s"
    Add-Content -LiteralPath $log -Value $line
    Write-Host $s
}

try {
    Log 'Starting read-only UVC diagnostic'
    Get-CimInstance Win32_PnPEntity |
        Where-Object { $_.PNPDeviceID -match 'VID_0BDA&PID_5830|VID_0BDA&PID_5840' } |
        Select-Object Name, PNPDeviceID, Status, Service, Manufacturer |
        Format-List |
        Out-File (Join-Path $out 'device_pnp.txt') -Encoding utf8

    Get-PnpDevice -PresentOnly |
        Where-Object { $_.InstanceId -match 'VID_0BDA&PID_5830|VID_0BDA&PID_5840' } |
        ForEach-Object {
            $id = $_.InstanceId
            "DEVICE: $id"
            Get-PnpDeviceProperty -InstanceId $id -ErrorAction Continue |
                Where-Object { $_.KeyName -match 'HardwareIds|CompatibleIds|Service|Driver|Class|Location|Parent|Capabilities' } |
                Select-Object KeyName, Data |
                Format-List
        } | Out-File (Join-Path $out 'pnp_properties.txt') -Encoding utf8

    $ff = Get-Command ffmpeg.exe -ErrorAction SilentlyContinue
    if ($null -ne $ff) {
        Log "FFmpeg found: enumerating DirectShow devices (read-only)."
        & $ff.Source -hide_banner -list_devices true -f dshow -i dummy 2>&1 |
            Out-File (Join-Path $out 'dshow_devices.txt') -Encoding utf8
    } else {
        Log 'FFmpeg not found; skipping optional DirectShow enumeration.'
    }

    Log 'Done. Review output files for any hardware IDs before sharing publicly.'
    Write-Host "Output folder: $out"
} catch {
    Log "ERROR: $_"
    throw
}
