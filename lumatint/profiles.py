"""Pure, testable color profile and gamma-ramp math."""

from dataclasses import asdict, dataclass
from math import log
from typing import List, Sequence, Tuple


@dataclass(frozen=True)
class ColorProfile:
    temperature: int = 6500
    brightness: int = 100
    gamma: float = 1.0
    red: int = 100
    green: int = 100
    blue: int = 100

    @classmethod
    def from_dict(cls, data: dict) -> "ColorProfile":
        if not isinstance(data, dict):
            return cls()
        defaults = asdict(cls())
        values = {key: data.get(key, value) for key, value in defaults.items()}
        try:
            return cls(
                temperature=max(4200, min(8500, int(values["temperature"]))),
                brightness=max(80, min(110, int(values["brightness"]))),
                gamma=max(0.85, min(1.15, float(values["gamma"]))),
                red=max(88, min(112, int(values["red"]))),
                green=max(88, min(112, int(values["green"]))),
                blue=max(88, min(112, int(values["blue"]))),
            )
        except (ValueError, TypeError, OverflowError):
            return cls()


PRESETS = {
    "Neutral": ColorProfile(),
    "Warm": ColorProfile(temperature=5100, brightness=98),
    "Cool": ColorProfile(temperature=8000),
    "Night": ColorProfile(temperature=4400, brightness=87, gamma=0.95),
    "Soft": ColorProfile(temperature=5900, brightness=95, gamma=1.05),
}


def _kelvin_rgb(kelvin: int) -> Tuple[float, float, float]:
    temperature = max(1000, min(40000, kelvin)) / 100.0
    if temperature <= 66:
        red = 255.0
        green = 99.4708025861 * log(temperature) - 161.1195681661
    else:
        red = 329.698727446 * pow(temperature - 60.0, -0.1332047592)
        green = 288.1221695283 * pow(temperature - 60.0, -0.0755148492)
    if temperature >= 66:
        blue = 255.0
    elif temperature <= 19:
        blue = 0.0
    else:
        blue = 138.5177312231 * log(temperature - 10.0) - 305.0447927307
    return tuple(max(1.0, min(255.0, value)) for value in (red, green, blue))


def color_gains(profile: ColorProfile) -> Tuple[float, float, float]:
    neutral = _kelvin_rgb(6500)
    actual = _kelvin_rgb(profile.temperature)
    balance = (profile.red, profile.green, profile.blue)
    return tuple((actual[i] / neutral[i]) * balance[i] / 100.0 for i in range(3))


def identity_ramp() -> List[List[int]]:
    return [[int(round(index * 65535 / 255)) for index in range(256)] for _ in range(3)]


def make_ramp(profile: ColorProfile, original: Sequence[Sequence[int]]) -> List[List[int]]:
    """Apply a gentle correction to the originally captured Windows gamma ramp.

    Uses the captured ramp instead of overwriting color calibration with identity.
    Values are clamped to stay within the visible hardware range.
    """
    if len(original) != 3 or any(len(channel) != 256 for channel in original):
        raise ValueError("Expected 3 channels with 256 ramp values each")
    gains = color_gains(profile)
    brightness = profile.brightness / 100.0
    exponent = 1.0 / profile.gamma
    result = []
    for channel in range(3):
        values = []
        for value in original[channel]:
            normalized = max(0.0, min(1.0, value / 65535.0))
            scaled = pow(normalized, exponent) * gains[channel] * brightness
            # Stay within Windows GDI safety heuristics: each output should
            # remain near the linear ramp for its corresponding input.
            linear = round(len(values) * 65535 / 255)
            raw = int(round(max(0.0, min(1.0, scaled)) * 65535))
            values.append(max(0, min(65535, max(linear - 31000, min(linear + 31000, raw)))))
        result.append(values)
    return result
