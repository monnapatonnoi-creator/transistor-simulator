import unittest

from dc_bias import (
    BIAS_REGISTRY,
    REGION_LABELS,
    VCE_SAT,
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


CUTOFF = BiasParams(vcc=5.0, r1=100e3, r2=5e3, rc=2.2e3, re=1e3, beta=100.0, vbe=0.70)
SATURATED = BiasParams(vcc=12.0, r1=100e3, r2=22e3, rc=10e3, re=1e3, beta=100.0, vbe=0.70)


class TestRegion(unittest.TestCase):
    def test_cutoff_labelled_and_values_left_raw(self):
        r = calculate("voltage_divider", CUTOFF)
        self.assertEqual(r.region, "cutoff")
        self.assertTrue(r.warnings)
        self.assertAlmostEqual(r.ib, -4.367402e-06, delta=1e-11)  # raw, negative, not corrected
        self.assertAlmostEqual(r.vce, 6.401936, places=5)

    def test_saturation_labelled_and_values_left_raw(self):
        r = calculate("voltage_divider", SATURATED)
        self.assertEqual(r.region, "saturation")
        self.assertTrue(r.warnings)
        self.assertAlmostEqual(r.vce, -1.540738, places=5)  # VCE <= VCE_SAT
        self.assertLess(r.vce, VCE_SAT)

    def test_ib_exactly_zero_is_cutoff(self):
        # Exact-arithmetic boundary case: VTH = 1.0*3/(1+3) = 0.75 exactly, VBE = 0.75
        # exactly, so IB = 0.0 and the region must be cutoff, not active.
        p = BiasParams(vcc=1.0, r1=1.0, r2=3.0, rc=100.0, re=100.0, beta=100.0, vbe=0.75)
        r = calculate("voltage_divider", p)
        self.assertEqual(r.ib, 0.0)
        self.assertEqual(r.region, "cutoff")
        self.assertTrue(r.warnings)

    def test_active_has_no_warnings(self):
        r = calculate("voltage_divider", REFERENCE)
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, ())

    def test_region_labels_cover_every_region(self):
        self.assertEqual(REGION_LABELS["active"], "Forward Active")
        self.assertEqual(set(REGION_LABELS), {"active", "cutoff", "saturation"})


if __name__ == "__main__":
    unittest.main()
