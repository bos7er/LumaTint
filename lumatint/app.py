"""Modern English-language user interface for LumaTint."""

import sys
import threading
from pathlib import Path
from tkinter import BooleanVar, DoubleVar, messagebox

import customtkinter as ctk

from .profiles import ColorProfile, PRESETS, color_gains, make_ramp
from .settings import load_settings, save_settings
from .windows import DisplayError, WindowsGamma, is_startup_enabled, set_startup

BG = "#0B1020"
CARD = "#151D30"
PANEL = "#10182A"
LINE = "#29334B"
TEXT = "#EFF4FF"
MUTED = "#91A0BC"
ACCENT = "#7C78FF"
SUCCESS = "#6DE6B0"
WARNING = "#FFBC77"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class LumaTintApp(ctk.CTk):
    def __init__(self, start_minimized: bool = False) -> None:
        super().__init__()
        self.title("LumaTint - Display Color Control")
        self.geometry("1050x735")
        self.minsize(885, 650)
        self.configure(fg_color=BG)
        if start_minimized:
            self.withdraw()
        self._set_icon()
        self.protocol("WM_DELETE_WINDOW", self._hide_or_exit)
        self.bind("<Control-Shift-R>", lambda _event: self.restore_original())
        self._after_apply = None
        self._guard = False
        self._tray = None
        self._tray_thread = None
        self._exiting = False
        self._driver = None
        self._driver_error = None
        self._start_minimized = start_minimized

        settings = load_settings()
        self.profile = settings["profile"]
        self.preset = settings["preset"]
        self.enabled = BooleanVar(value=settings["enabled"])
        self.startup = BooleanVar(value=is_startup_enabled())
        self.slider_vars = {
            "temperature": DoubleVar(value=self.profile.temperature),
            "brightness": DoubleVar(value=self.profile.brightness),
            "gamma": DoubleVar(value=self.profile.gamma),
            "red": DoubleVar(value=self.profile.red),
            "green": DoubleVar(value=self.profile.green),
            "blue": DoubleVar(value=self.profile.blue),
        }
        self.value_labels = {}
        self.preset_buttons = {}

        try:
            self._driver = WindowsGamma()
        except DisplayError as exc:
            self._driver_error = str(exc)
        self._build_layout()
        self._sync_ui()
        if self.enabled.get():
            self._apply()
        else:
            self._set_status("Ready to customize", SUCCESS)
        self.after(180, self._start_tray)

    def _set_icon(self) -> None:
        try:
            base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
            icon = base / "assets" / "lumatint.ico"
            if icon.exists():
                self.iconbitmap(str(icon))
        except Exception:
            pass

    def _build_layout(self) -> None:
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=25, pady=23)
        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.pack(fill="x", pady=(0, 18))
        logo = ctk.CTkFrame(header, width=52, height=52, corner_radius=17, fg_color=ACCENT)
        logo.pack(side="left")
        logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="◈", font=ctk.CTkFont(size=31, weight="bold"), text_color="white").pack(expand=True)
        titles = ctk.CTkFrame(header, fg_color="transparent")
        titles.pack(side="left", padx=15)
        ctk.CTkLabel(titles, text="LumaTint", text_color=TEXT, font=ctk.CTkFont(size=29, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(titles, text="Your screen, your atmosphere.", text_color=MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w")
        ctk.CTkLabel(header, text="WINDOWS 10 / 11   •   v1.0", text_color=MUTED, font=ctk.CTkFont(size=11)).pack(side="right")

        layout = ctk.CTkFrame(outer, fg_color="transparent")
        layout.pack(fill="both", expand=True)
        sidebar = ctk.CTkFrame(layout, fg_color=PANEL, width=236, corner_radius=20, border_color=LINE, border_width=1)
        sidebar.pack(side="left", fill="y", padx=(0, 17))
        sidebar.pack_propagate(False)
        ctk.CTkLabel(sidebar, text="QUICK PRESETS", font=ctk.CTkFont(size=12, weight="bold"), text_color=MUTED).pack(anchor="w", padx=20, pady=(25, 14))
        descriptions = {"Neutral": "Original balance", "Warm": "Cozy evenings", "Cool": "Crisp & focused", "Night": "Gentle after dark", "Soft": "Reduced intensity"}
        for name in PRESETS:
            button = ctk.CTkButton(
                sidebar, text=f"{name}  ·  {descriptions[name]}", anchor="w", height=49,
                fg_color="transparent", hover_color="#222C45", text_color=TEXT,
                corner_radius=11, font=ctk.CTkFont(size=12),
                command=lambda n=name: self.select_preset(n),
            )
            button.pack(fill="x", padx=11, pady=4)
            self.preset_buttons[name] = button
        ctk.CTkFrame(sidebar, height=1, fg_color=LINE).pack(fill="x", padx=18, pady=(18, 16))
        ctk.CTkLabel(sidebar, text="DISPLAY EFFECT", font=ctk.CTkFont(size=12, weight="bold"), text_color=MUTED).pack(anchor="w", padx=20, pady=(0, 12))
        self.enabled_switch = ctk.CTkSwitch(
            sidebar, text="Enable color changes", variable=self.enabled,
            command=self._toggle_enabled, progress_color=ACCENT,
            font=ctk.CTkFont(size=12), text_color=TEXT,
        )
        self.enabled_switch.pack(anchor="w", padx=19, pady=(0, 20))
        ctk.CTkLabel(
            sidebar, text="Changes are restored when\nyou fully quit the app.", justify="left",
            text_color=MUTED, font=ctk.CTkFont(size=11),
        ).pack(side="bottom", anchor="w", padx=20, pady=25)

        main = ctk.CTkScrollableFrame(layout, fg_color="transparent", scrollbar_button_color=LINE)
        main.pack(side="left", fill="both", expand=True)
        status_box = ctk.CTkFrame(main, fg_color=CARD, corner_radius=17, border_color=LINE, border_width=1)
        status_box.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(status_box, text="DISPLAY STATUS", font=ctk.CTkFont(size=11, weight="bold"), text_color=MUTED).pack(anchor="w", padx=20, pady=(18, 4))
        self.status_label = ctk.CTkLabel(status_box, text="Initializing...", font=ctk.CTkFont(size=15, weight="bold"), text_color=SUCCESS, wraplength=550)
        self.status_label.pack(anchor="w", padx=20, pady=(0, 18))

        preview_frame = ctk.CTkFrame(main, fg_color=CARD, corner_radius=17, border_color=LINE, border_width=1)
        preview_frame.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(preview_frame, text="COLOR PREVIEW", font=ctk.CTkFont(size=11, weight="bold"), text_color=MUTED).pack(anchor="w", padx=20, pady=(15, 0))
        self.preview = ctk.CTkFrame(preview_frame, height=62, corner_radius=12, fg_color="#D6E0FA")
        self.preview.pack(fill="x", padx=20, pady=(10, 8))
        self.preview.pack_propagate(False)
        self.preview_text = ctk.CTkLabel(self.preview, text="Balanced whites · Smooth tones", text_color="#1E293B", font=ctk.CTkFont(size=14, weight="bold"))
        self.preview_text.pack(expand=True)
        ctk.CTkLabel(preview_frame, text="Preview is approximate. Actual results depend on your display.", text_color=MUTED, font=ctk.CTkFont(size=10)).pack(anchor="w", padx=20, pady=(0, 14))

        controls = ctk.CTkFrame(main, fg_color=CARD, corner_radius=17, border_color=LINE, border_width=1)
        controls.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(controls, text="FINE-TUNE YOUR DISPLAY", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT).pack(anchor="w", padx=20, pady=(17, 3))
        ctk.CTkLabel(controls, text="Adjust and see changes immediately.", text_color=MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", padx=20)
        self._add_slider(controls, "temperature", "Color temperature", 4200, 8500, "K")
        self._add_slider(controls, "brightness", "Software brightness", 80, 110, "%")
        self._add_slider(controls, "gamma", "Gamma", 0.85, 1.15, "")
        ctk.CTkFrame(controls, height=1, fg_color=LINE).pack(fill="x", padx=20, pady=11)
        for key in ("red", "green", "blue"):
            self._add_slider(controls, key, f"{key.capitalize()} channel", 88, 112, "%")
        ctk.CTkFrame(controls, fg_color="transparent", height=7).pack()

        actions = ctk.CTkFrame(main, fg_color=CARD, corner_radius=17, border_color=LINE, border_width=1)
        actions.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(actions, text="STARTUP & RECOVERY", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT).pack(anchor="w", padx=20, pady=(18, 10))
        ctk.CTkSwitch(
            actions, text="Launch LumaTint when I sign in", variable=self.startup,
            command=self._toggle_startup, progress_color=ACCENT,
            font=ctk.CTkFont(size=12), text_color=TEXT,
        ).pack(anchor="w", padx=19, pady=(0, 9))
        ctk.CTkLabel(
            actions, text="Starts minimized to the system tray. No administrator access needed.",
            text_color=MUTED, font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=20, pady=(0, 17))
        row = ctk.CTkFrame(actions, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkButton(row, text="Restore original colors", height=38, corner_radius=10,
                      fg_color="#252E44", hover_color="#333F5A", text_color=TEXT,
                      command=self.restore_original).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Reapply", height=38, width=103, corner_radius=10,
                      fg_color=ACCENT, hover_color="#645FE8", command=self._apply).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Quit", height=38, width=76, corner_radius=10,
                      fg_color="#252E44", hover_color="#333F5A", command=self._quit).pack(side="right")
        ctk.CTkLabel(main, text="Local settings only  •  No tracking  •  Primary display  •  MIT licensed", text_color=MUTED, font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(0, 12))

    def _add_slider(self, parent, key: str, title: str, minval: float, maxval: float, suffix: str) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(14, 0))
        ctk.CTkLabel(row, text=title, font=ctk.CTkFont(size=12), text_color=TEXT).pack(side="left")
        value = ctk.CTkLabel(row, width=66, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color="#A8A7FF")
        value.pack(side="right")
        self.value_labels[key] = (value, suffix)
        ctk.CTkSlider(
            parent, from_=minval, to=maxval, variable=self.slider_vars[key], height=15,
            progress_color=ACCENT, button_color="#AAA8FF", button_hover_color="white",
            command=lambda _v, k=key: self._on_slider(k),
        ).pack(fill="x", padx=20, pady=(7, 0))

    def _values_to_profile(self) -> ColorProfile:
        return ColorProfile.from_dict({name: variable.get() for name, variable in self.slider_vars.items()})

    def _sync_ui(self) -> None:
        for key, variable in self.slider_vars.items():
            value, suffix = self.value_labels[key]
            number = variable.get()
            value.configure(text=f"{number:.2f}" if key == "gamma" else f"{round(number)}{suffix}")
        for name, button in self.preset_buttons.items():
            selected = self.preset == name
            button.configure(fg_color="#2B3058" if selected else "transparent")
        red, green, blue = color_gains(self._values_to_profile())
        r = max(0, min(255, round(210 * red)))
        g = max(0, min(255, round(220 * green)))
        b = max(0, min(255, round(243 * blue)))
        self.preview.configure(fg_color=f"#{r:02x}{g:02x}{b:02x}")
        self.preview_text.configure(text=f"{self.preset}  ·  {round(self.slider_vars['temperature'].get())} K")

    def _on_slider(self, _key: str) -> None:
        if self._guard:
            return
        self.preset = "Custom"
        self.profile = self._values_to_profile()
        self._sync_ui()
        self._queue_apply()

    def select_preset(self, name: str) -> None:
        self.preset = name
        self.profile = PRESETS[name]
        self._guard = True
        try:
            for key, variable in self.slider_vars.items():
                variable.set(getattr(self.profile, key))
            self.enabled.set(True)
        finally:
            self._guard = False
        self._sync_ui()
        self._queue_apply()

    def _toggle_enabled(self) -> None:
        if not self.enabled.get():
            self.restore_original()
        else:
            self._queue_apply()

    def _queue_apply(self) -> None:
        if self._after_apply is not None:
            self.after_cancel(self._after_apply)
        self._after_apply = self.after(170, self._apply)

    def _apply(self) -> None:
        self._after_apply = None
        self.profile = self._values_to_profile()
        if self.enabled.get():
            if self._driver_error:
                self._set_status(self._driver_error, WARNING)
                self._persist()
                return
            try:
                ramp = make_ramp(self.profile, self._driver.original)
                if ramp == self._driver.original:
                    self._driver.restore()
                else:
                    self._driver.apply(ramp)
                self._set_status("Color settings applied to primary display", SUCCESS)
            except (DisplayError, OSError) as exc:
                self._set_status(str(exc), WARNING)
        else:
            self._set_status("Effect disabled", MUTED)
        self._persist()

    def restore_original(self) -> None:
        if self._after_apply is not None:
            self.after_cancel(self._after_apply)
            self._after_apply = None
        self.enabled.set(False)
        if self._driver:
            try:
                self._driver.restore()
                self._set_status("Original display colors restored", SUCCESS)
            except DisplayError as exc:
                self._set_status(str(exc), WARNING)
        else:
            self._set_status("Effect disabled", MUTED)
        self._persist()

    def _persist(self) -> None:
        try:
            save_settings(self.enabled.get(), self._values_to_profile(), self.preset)
        except OSError as exc:
            self._set_status(f"Could not save settings: {exc}", WARNING)

    def _toggle_startup(self) -> None:
        try:
            set_startup(self.startup.get())
        except OSError as exc:
            self.startup.set(is_startup_enabled())
            messagebox.showerror("Startup setup failed", str(exc))
            return
        self._set_status("Windows startup setting updated", SUCCESS)

    def _set_status(self, message: str, color: str) -> None:
        self.status_label.configure(text=message, text_color=color)

    def _start_tray(self) -> None:
        try:
            import pystray
            from PIL import Image
            base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
            png = base / "assets" / "lumatint.png"
            img = Image.open(png).convert("RGBA")
            menu = pystray.Menu(
                pystray.MenuItem("Open LumaTint", lambda _icon, _item: self.after(0, self._show), default=True),
                pystray.MenuItem("Restore original colors", lambda _icon, _item: self.after(0, self.restore_original)),
                pystray.MenuItem("Quit and restore", lambda _icon, _item: self.after(0, self._quit)),
            )
            self._tray = pystray.Icon("LumaTint", img, "LumaTint - Display Color Control", menu)
            self._tray_thread = threading.Thread(target=self._tray.run, daemon=True)
            self._tray_thread.start()
        except Exception:
            self._tray = None
        if self._start_minimized:
            if self._tray is not None:
                self.withdraw()
            else:
                self.deiconify()
                self.iconify()

    def _show(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def _hide_or_exit(self) -> None:
        if self._tray is not None:
            self.withdraw()
        else:
            self._quit()

    def _quit(self) -> None:
        if self._exiting:
            return
        self._exiting = True
        if self._after_apply is not None:
            self.after_cancel(self._after_apply)
            self._after_apply = None
        self._persist()  # Preserve the user's choice for the next session.
        if self._driver:
            try:
                self._driver.restore()
            except DisplayError:
                pass
        if self._tray:
            try:
                self._tray.stop()
            except Exception:
                pass
        self.destroy()
