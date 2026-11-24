import unittest

from spice_engine import (
    MODEL_LINE,
    MODEL_NAME,
    InvalidInput,
    SimInput,
    build_netlist,
)


REFERENCE = dict(
    vcc=12.0,
    r1=100_000.0,
    r2=22_000.0,
    rc=2_200.0,
    re=1_000.0,
    rl=10_000.0,
    cin_f=10e-6,
    cout_f=10e-6,
    amplitude_v=0.010,
    freq_hz=1_000.0,
)


class TestNetlistBuilder(unittest.TestCase):
    def test_reference_netlist_contains_expected_nodes_and_directives(self):
        params = SimInput(**REFERENCE)
        netlist = build_netlist(params, "dc")

        for token in ("VCC", "R1", "R2", "RC", "RE", "RL", "CIN", "COUT",
                      "Q1", MODEL_NAME, ".op", ".end"):
            self.assertIn(token, netlist)
        self.assertIn("vcc base", netlist)   # R1: collector supply to base
        self.assertIn("base 0", netlist)     # R2: base to ground
        self.assertIn("emi 0", netlist)      # RE: emitter to ground
        self.assertIn("col base emi", netlist)  # Q1 collector/base/emitter
        self.assertIn("in base", netlist)    # CIN feeds the base node
        self.assertIn("col out", netlist)    # COUT feeds the load

        self.assertIn(".ac dec", build_netlist(params, "ac"))
        tran = build_netlist(params, "tran")
        self.assertIn(".tran", tran)
        self.assertIn("SIN(0 0.01 1000)", tran)
        self.assertIn(MODEL_LINE, netlist)

    def test_rejects_nonpositive_passives(self):
        for field, value in (("re", 0.0), ("rl", -1.0), ("amplitude_v", 0.0),
                             ("freq_hz", 0.0), ("freq_hz", 200_000.0)):
            with self.subTest(field=field, value=value):
                bad = dict(REFERENCE)
                bad[field] = value
                with self.assertRaises(InvalidInput):
                    SimInput(**bad)

    def test_rejects_non_numeric_form_text(self):
        bad = dict(REFERENCE)
        bad["re"] = "1; rm -rf"
        with self.assertRaises((InvalidInput, TypeError)):
            SimInput(**bad)

    def test_unknown_analysis(self):
        params = SimInput(**REFERENCE)
        with self.assertRaises(InvalidInput):
            build_netlist(params, "bode")


if __name__ == "__main__":
    unittest.main()
