"""Real ngspice integration checks; skipped when the engine is unavailable."""

import math
import os
import shutil
import unittest

from spice_engine import SimInput, find_ngspice, run_analysis

BASE = dict(
    vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0, re=1_000.0,
    rl=10_000.0, cin_f=10e-6, cout_f=10e-6, amplitude_v=0.010, freq_hz=1_000.0,
)


def available() -> bool:
    return bool(os.environ.get("NGSPICE_EXE") or shutil.which("ngspice")
                or find_ngspice())


@unittest.skipUnless(available(), "ngspice is not installed")
class TestRealNgspice(unittest.TestCase):
    def test_all_analyses_produce_real_nonempty_data(self):
        params = SimInput(**BASE)
        op = run_analysis(params, "dc")
        ac = run_analysis(params, "ac")
        tran = run_analysis(params, "tran")
        self.assertGreater(op.op.ic, 0)
        self.assertGreater(ac.ac[0].gain_mag, 0)
        self.assertTrue(all(math.isfinite(p.gain_db) for p in ac.ac))
        self.assertGreater(len(tran.tran), 200)
        self.assertTrue(all(math.isfinite(p.vout_v) for p in tran.tran))
        for result in (op, ac, tran):
            self.assertIn("ngspice-47", result.version)
            self.assertIn(".end", result.netlist)

    def test_changing_re_changes_real_results(self):
        before = run_analysis(SimInput(**BASE), "dc").op
        changed = dict(BASE, re=2_000.0)
        after = run_analysis(SimInput(**changed), "dc").op
        self.assertLess(after.ic, before.ic)
        self.assertNotAlmostEqual(after.vb, before.vb, places=3)

    def test_changing_amplitude_changes_real_waveform(self):
        before = run_analysis(SimInput(**BASE), "tran").tran
        changed = dict(BASE, amplitude_v=0.020)
        after = run_analysis(SimInput(**changed), "tran").tran
        self.assertGreater(max(abs(p.vin_v) for p in after),
                           max(abs(p.vin_v) for p in before) * 1.8)
        self.assertGreater(max(abs(p.vout_v) for p in after),
                           max(abs(p.vout_v) for p in before) * 1.8)


if __name__ == "__main__":
    unittest.main()
