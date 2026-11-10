import unittest

from units import fmt_current, fmt_resistance, fmt_voltage


class TestFormatting(unittest.TestCase):
    def test_microamp_range(self):
        self.assertEqual(fmt_current(1.229858e-05), "12.3 µA")
        self.assertEqual(fmt_current(-4.367402e-06), "-4.37 µA")

    def test_milliamp_range(self):
        self.assertEqual(fmt_current(1.229858e-03), "1.23 mA")
        self.assertEqual(fmt_current(1.060325e-03), "1.06 mA")

    def test_amp_range(self):
        self.assertEqual(fmt_current(0.5), "500 mA")

    def test_voltage_three_sig_figs(self):
        self.assertEqual(fmt_voltage(8.0521553505), "8.05 V")
        self.assertEqual(fmt_voltage(12.0), "12.0 V")

    def test_resistance_ranges(self):
        self.assertEqual(fmt_resistance(18032.786885), "18.0 kΩ")
        self.assertEqual(fmt_resistance(1000.0), "1.00 kΩ")
        self.assertEqual(fmt_resistance(470.0), "470 Ω")
        self.assertEqual(fmt_resistance(10e6), "10.0 MΩ")

    def test_no_scientific_notation(self):
        for text in (fmt_current(1e-7), fmt_resistance(10e6), fmt_voltage(1e-3)):
            self.assertNotIn("e", text.replace("µ", "").lower())


if __name__ == "__main__":
    unittest.main()
