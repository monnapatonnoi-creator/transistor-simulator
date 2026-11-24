import math
import unittest
from pathlib import Path

from spice_engine import (
    AcPoint,
    ParseFailed,
    find_cutoff,
    parse_ac,
    parse_op,
    parse_tran,
)

FIXTURES = Path(__file__).parent / "fixtures"
DC_RAW = (FIXTURES / "lab4_dc.raw").read_text(encoding="utf-8")
AC_RAW = (FIXTURES / "lab4_ac.raw").read_text(encoding="utf-8")
TRAN_RAW = (FIXTURES / "lab4_tran.raw").read_text(encoding="utf-8")


class TestParsers(unittest.TestCase):
    def test_parse_op_values(self):
        op = parse_op(DC_RAW)
        self.assertAlmostEqual(op.vb, 1.949112053392557, places=6)
        self.assertAlmostEqual(op.ve, 1.289453694188224, places=6)
        self.assertAlmostEqual(op.vc, 9.189410182055312, places=6)
        self.assertAlmostEqual(op.vce, op.vc - op.ve, places=9)
        self.assertAlmostEqual(op.ic, 1.277540826338495e-3, places=9)
        self.assertGreater(op.ic, 0)

    def test_parse_ac_uses_input_columns(self):
        points = parse_ac(AC_RAW)
        self.assertGreater(len(points), 50)
        for point in points:
            self.assertIsInstance(point, AcPoint)
            self.assertGreater(point.freq_hz, 0)
            self.assertAlmostEqual(point.gain_mag, 10 ** (point.gain_db / 20), places=8)

        # Synthetic two-point raw: output 10x input, same phase -> +20 dB, 0 deg.
        synthetic = """Title: synthetic
Plotname: AC Analysis
Flags: complex
No. Variables: 3
No. Points: 1
Variables:
\t0\tfrequency\tfrequency\tgrid=3
\t1\tv(in)\tvoltage
\t2\tv(out)\tvoltage
Values:
0\t1.000000000000000e+03,0.000000000000000e+00
\t2.000000000000000e+00,0.000000000000000e+00
\t2.000000000000000e+01,0.000000000000000e+00
"""
        point = parse_ac(synthetic)[0]
        self.assertEqual(point.freq_hz, 1000.0)
        self.assertAlmostEqual(point.gain_db, 20.0, places=6)
        self.assertAlmostEqual(point.phase_deg, 0.0, places=6)

    def test_parse_tran_pairs(self):
        points = parse_tran(TRAN_RAW)
        self.assertGreater(len(points), 200)
        self.assertTrue(all(p.time_s >= 0 for p in points))
        self.assertTrue(all(points[i].time_s < points[i + 1].time_s
                            for i in range(len(points) - 1)))
        self.assertAlmostEqual(max(abs(p.vin_v) for p in points), 0.010, places=4)
        # Vout is AC-coupled (zero DC), centred on 0 V and inverted vs Vin.
        self.assertGreater(max(abs(p.vout_v) for p in points), 0.001)
        self.assertLess(sum(p.vin_v * p.vout_v for p in points), 0.0)

    def test_no_cutoff_returns_none(self):
        flat = [AcPoint(freq_hz=f, gain_db=20.0, gain_mag=10.0, phase_deg=0.0)
                for f in (10.0, 100.0, 1000.0, 10_000.0)]
        self.assertIsNone(find_cutoff(flat))

    def test_real_sweep_has_no_cutoff_in_range(self):
        # With the reference values and demo model the 10 Hz-10 MHz sweep is flat;
        # the handout requires an honest "not determined" result, not a guess.
        self.assertIsNone(find_cutoff(parse_ac(AC_RAW)))

    def test_cutoff_found_from_synthetic_sweep(self):
        gains = [(10.0, 20.0), (100.0, 20.0), (1000.0, 19.0), (10_000.0, 14.0)]
        points = [AcPoint(f, g, 10 ** (g / 20), -180.0) for f, g in gains]
        self.assertEqual(find_cutoff(points), 10_000.0)

    def test_parse_rejects_missing_columns(self):
        broken = DC_RAW.replace("v(base)", "v(missing)")
        with self.assertRaises(ParseFailed):
            parse_op(broken)


if __name__ == "__main__":
    unittest.main()
