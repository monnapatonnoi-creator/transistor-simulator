import unittest

from dc_bias import BiasParams, voltage_divider

REFERENCE = BiasParams(vcc=12.0, r1=100e3, r2=22e3, rc=2.2e3, re=1e3, beta=100.0, vbe=0.70)


class TestVoltageDivider(unittest.TestCase):
    def test_reference_operating_point(self):
        r = voltage_divider(REFERENCE)
        self.assertAlmostEqual(r.vth, 2.1639344262, places=8)
        self.assertAlmostEqual(r.rth, 18032.786885, delta=1e-3)
        self.assertAlmostEqual(r.ib, 1.229858e-05, delta=1e-11)
        self.assertAlmostEqual(r.ic, 1.229858e-03, delta=1e-9)
        self.assertAlmostEqual(r.ie, 1.242157e-03, delta=1e-9)
        self.assertAlmostEqual(r.ve, 1.2421567277, places=6)
        self.assertAlmostEqual(r.vb, 1.9421567277, places=6)
        self.assertAlmostEqual(r.vc, 9.2943120782, places=6)
        self.assertAlmostEqual(r.vce, 8.0521553505, places=6)
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, ())


if __name__ == "__main__":
    unittest.main()
