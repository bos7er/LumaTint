<div align="center">
  <img src="assets/lumatint.png" alt="LumaTint logo" width="108" />

  # LumaTint

  **Your screen, your atmosphere.**

  A clean, free Windows desktop app for adjusting display color temperature, gamma, brightness, and RGB balance.

  [![Build LumaTint EXE](https://github.com/bos7er/LumaTint/actions/workflows/build-windows.yml/badge.svg)](https://github.com/bos7er/LumaTint/actions/workflows/build-windows.yml)
  ![Windows 10/11](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-5865F2)
  ![MIT License](https://img.shields.io/badge/license-MIT-5dd6a2)

  **[⬇ Download for Windows](https://github.com/bos7er/LumaTint/releases/latest)** · **[🌐 Website](https://bos7er.github.io/LumaTint/)** · **[⚙ Actions](https://github.com/bos7er/LumaTint/actions)**
</div>

---

## Features

- **Five presets:** Neutral, Warm, Cool, Night, and Soft.
- **Live controls:** Color temperature (4200–8500 K), software brightness, gamma, and red/green/blue balance.
- **Starts with Windows (optional):** Enable auto-start from the app. It launches minimized to the system tray on your next sign-in.
- **System tray:** Keep LumaTint running without leaving a window open. Open, restore the display, or quit from the tray menu.
- **Safe recovery:** Capture the original display gamma ramp and restore it when you disable the effect or fully quit.
- **Local-only settings:** Saved under `%LOCALAPPDATA%\LumaTint\settings.json`. No account, cloud, tracking, or admin rights.
- **Portable EXE:** No Python installation required for people downloading the release.

## Download and run

1. Open **[Releases](https://github.com/bos7er/LumaTint/releases/latest)**.
2. Download `LumaTint.exe`.
3. Move the EXE to a **permanent folder**, for example `C:\Apps\LumaTint\`, especially if you plan to enable startup.
4. Double-click the EXE and choose a preset. Windows may display a warning for unsigned software.
5. In **STARTUP & RECOVERY**, enable **Launch LumaTint when I sign in** if you want it to run at sign-in.

**Note:** The Releases download becomes available after the maintainer publishes the first `v1.0.0` release tag. Until then, you can get a preview EXE via **Actions → Build LumaTint EXE → Artifacts**.

## Important limitations

LumaTint modifies the **primary display's hardware gamma ramp** using the Windows GDI `SetDeviceGammaRamp` API. This is a small, system-wide correction, **not** hardware backlight control or a true saturation/vibrance adjustment. Support depends on your display driver.

Microsoft discourages this legacy API for advanced color management because:

- The call can report success even when the driver ignores it.
- **HDR**, **Windows Night light**, ICC calibration, manufacturer color tools, and some games can interfere.
- Monitor changes, sleep/wake, and graphics driver resets may cancel the effect; use **Reapply** if needed.
- A color ramp may continue after a crash; sign out, change display mode, or reopen LumaTint and restore the original colors.
- Only the primary display is adjusted in v1.0.

These details are documented by [Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-setdevicegammaramp). Disable HDR and Night light while testing if you do not see a difference.

## Build from source

Requires Python 3.12 on Windows:

```powershell
py -m pip install -r requirements.txt
py main.py
```

To build `dist\LumaTint.exe` locally, double-click `build.bat` or run:

```powershell
py -m pip install -r requirements-build.txt
py -m PyInstaller --noconfirm --clean --onefile --windowed --name LumaTint --icon assets/lumatint.ico --add-data "assets;assets" --collect-all customtkinter main.py
```

## GitHub Actions: build and publish

The workflow is located at **`.github/workflows/build-windows.yml`**. GitHub only recognizes workflows in that exact directory.

- **Build on every push to `main`:** Actions → **Build LumaTint EXE** → the latest successful run → **Artifacts** → `LumaTint-Windows-EXE`.
- **Manual build:** Actions → **Build LumaTint EXE** → **Run workflow**.
- **Publish a public release:** Create a tag named `v1.0.0` (or later, `v1.0.1`). The workflow builds the EXE and attaches it automatically to a public GitHub Release using the repository's `GITHUB_TOKEN`. No personal token required.

For the first public release, create a tag **from the existing `main` commit**: GitHub → Releases → Draft a new release → Choose a tag → `v1.0.0` → create new tag from `main` → Publish release. The workflow then attaches the EXE when the tagged build succeeds.

## GitHub Pages website

The landing page lives in `docs/index.html` and contains only English copy. Enable it once:

**Settings → Pages → Build and deployment → Deploy from a branch → `main` → `/docs` → Save.**

The expected URL will be `https://bos7er.github.io/LumaTint/` if published under `bos7er/LumaTint`.

## How startup works

When enabled by the user, LumaTint adds **only its own value** to:

`HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`

It points to the current EXE with `--minimized`. Unchecking removes that value. The app **never modifies other apps' startup entries** and does not require admin rights. If you move or rename the EXE, disable and re-enable startup to update the path. Startup is configured only from the packaged EXE, not from a Python source run.

## Development

```powershell
py -m unittest discover -s tests -v
```

The math, profile validation, and JSON settings are covered by unit tests. The actual visual display effect and tray integration must also be tested on a real Windows PC; they cannot be fully validated by a CI runner.

## License

MIT — see [LICENSE](LICENSE).

> LumaTint is an independent open-source project and is not affiliated with Microsoft.
