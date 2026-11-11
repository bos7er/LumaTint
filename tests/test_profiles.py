import unittest

from lumatint.profiles import ColorProfile, PRESETS, color_gains, identity_ramp, make_ramp


class ColorProfileTests(unittest.TestCase):
    def test_presets_all_have_valid_ramps(self):
        for name, profile in PRESETS.items():
            with self.subTest(name=name):
                ramp = make_ramp(profile, identity_ramp())
                self.assertEqual(len(ramp), 3)
                self.assertTrue(all(len(channel) == 256 for channel in ramp))
                self.assertTrue(all(0 <= value <= 65535 for channel in ramp for value in channel))

    def test_neutral_preserves_original_ramp(self):
        original = identity_ramp()
        self.assertEqual(make_ramp(ColorProfile(), original), original)

    def test_warm_reduces_blue_relative_to_red(self):
        gains = color_gains(PRESETS["Warm"])
        self.assertGreater(gains[0], gains[2])

    def test_cool_reduces_red_relative_to_blue(self):
        gains = color_gains(PRESETS["Cool"])
        self.assertGreater(gains[2], gains[0])

    def test_invalid_input_shape_raises(self):
        with self.assertRaises(ValueError):
            make_ramp(ColorProfile(), [[1, 2, 3]])

    def test_values_are_clamped(self):
        profile = ColorProfile.from_dict({"temperature": -1, "brightness": 999, "gamma": 400,
                                          "red": 0, "green": 400, "blue": -3})
        self.assertEqual(profile.temperature, 4200)
        self.assertEqual(profile.brightness, 110)
        self.assertEqual(profile.gamma, 1.15)
        self.assertEqual((profile.red, profile.green, profile.blue), (88, 112, 88))

    def test_gdi_safety_deviation_limit(self):
        neutral = identity_ramp()
        extreme = ColorProfile(temperature=4200, brightness=80, gamma=0.85, red=88, green=88, blue=88)
        for row, reference in zip(make_ramp(extreme, neutral), neutral):
            self.assertTrue(all(abs(a - b) <= 31000 for a, b in zip(row, reference)))

    def test_no_abrupt_decrease_in_gamma_ramp(self):
        for profile in PRESETS.values():
            ramp = make_ramp(profile, identity_ramp())
            for channel in ramp:
                self.assertEqual(sorted(channel), channel)

    def test_original_ramp_does_not_mutate(self):
        original = identity_ramp()
        saved = [list(channel) for channel in original]
        make_ramp(PRESETS["Night"], original)
        self.assertEqual(original, saved)

    def test_non_numeric_profile_recovers_to_defaults(self):
        self.assertEqual(ColorProfile.from_dict({"gamma": "broken"}), ColorProfile())
