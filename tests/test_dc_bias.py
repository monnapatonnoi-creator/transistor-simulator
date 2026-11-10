import unittest

from dc_bias import (
    BIAS_REGISTRY,
    BiasInputError,
    BiasParams,
    UnknownBiasType,
    calculate,
    voltage_divider,
)

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


class TestValidation(unittest.TestCase):
    def test_zero_resistor_rejected(self):
        p = BiasParams(vcc=12.0, r1=100e3, r2=0.0, rc=2.2e3, re=1e3, beta=100.0)
        with self.assertRaises(BiasInputError) as ctx:
            calculate("voltage_divider", p)
        self.assertIn("r2 must be greater than zero", str(ctx.exception))

    def test_zero_beta_rejected(self):
        p = BiasParams(vcc=12.0, r1=100e3, r2=22e3, rc=2.2e3, re=1e3, beta=0.0)
        with self.assertRaises(BiasInputError) as ctx:
            calculate("voltage_divider", p)
        self.assertIn("beta must be greater than zero", str(ctx.exception))

    def test_negative_vcc_rejected(self):
        p = BiasParams(vcc=-1.0, r1=100e3, r2=22e3, rc=2.2e3, re=1e3, beta=100.0)
        with self.assertRaises(BiasInputError) as ctx:
            calculate("voltage_divider", p)
        self.assertIn("vcc must be greater than zero", str(ctx.exception))

    def test_vbe_at_or_above_vcc_rejected(self):
        p = BiasParams(vcc=12.0, r1=100e3, r2=22e3, rc=2.2e3, re=1e3, beta=100.0, vbe=12.0)
        with self.assertRaises(BiasInputError) as ctx:
            calculate("voltage_divider", p)
        self.assertIn("vbe must be less than vcc", str(ctx.exception))

    def test_unknown_bias_type_rejected(self):
        with self.assertRaises(UnknownBiasType):
            calculate("fixed_bias", REFERENCE)

    def test_registry_contains_voltage_divider(self):
        self.assertIn("voltage_divider", BIAS_REGISTRY)


if __name__ == "__main__":
    unittest.main()
