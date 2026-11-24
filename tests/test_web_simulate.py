import re
import unittest
from pathlib import Path
from unittest.mock import patch

import app as app_module
from spice_engine import (
    MODEL_NAME,
    NgspiceUnavailable,
    SimResult,
    parse_ac,
    parse_op,
    parse_tran,
)
from tests.test_web import REFERENCE_FORM

FIXTURES = Path(__file__).parent / "fixtures"
SIM_FORM = {
    "analysis": "dc",
    "sim_vcc": "12", "sim_r1": "100", "sim_r2": "22",
    "sim_rc": "2.2", "sim_re": "1", "sim_rl": "10",
    "sim_cin_uf": "10", "sim_cout_uf": "10",
    "sim_amplitude_mv": "10", "sim_freq_khz": "1",
}


def fixture_result(analysis: str) -> SimResult:
    raw = (FIXTURES / f"lab4_{analysis}.raw").read_text(encoding="utf-8")
    return SimResult(
        analysis=analysis,
        status="success",
        model=MODEL_NAME,
        netlist="* test netlist\n.op\n.end\n",
        log_excerpt="ngspice test log\n",
        version="ngspice-47, Build Aug 11 2026 13:49:23",
        op=parse_op(raw) if analysis == "dc" else None,
        ac=parse_ac(raw) if analysis == "ac" else [],
        tran=parse_tran(raw) if analysis == "tran" else [],
    )


def post(client, **changes):
    data = SIM_FORM.copy()
    data.update(changes)
    return client.post("/simulate", data=data)


def lab3_hidden_from(body):
    """Mimic the hidden Lab 3 inputs a browser submits with the SPICE form."""
    return dict(re.findall(r'name="(lab3_[^"]+)" value="([^"]*)"', body))


class TestSimulateRoute(unittest.TestCase):
    def setUp(self):
        self.client = app_module.create_app().test_client()

    def test_simulate_dc_shows_spice_values_and_labels(self):
        with patch.object(app_module, "run_analysis", return_value=fixture_result("dc")):
            resp = post(self.client, analysis="dc")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        for text in ("SPICE (ngspice)", "VB", "VCE", "IC", MODEL_NAME,
                     "Success", "test netlist", "data-testid=\"sim-result\""):
            self.assertIn(text, body)
        self.assertNotIn("Mock", body)

    def test_simulate_ac_has_axes_units_and_cutoff_message(self):
        with patch.object(app_module, "run_analysis", return_value=fixture_result("ac")):
            body = post(self.client, analysis="ac").get_data(as_text=True)
        self.assertIn('data-testid="bode-plot"', body)
        for text in ("Frequency (Hz)", "Gain (dB)", "Phase (deg)",
                     "Gain", "Phase", "not determined in sweep range"):
            self.assertIn(text, body)

    def test_simulate_tran_has_time_and_legend(self):
        with patch.object(app_module, "run_analysis", return_value=fixture_result("tran")):
            body = post(self.client, analysis="tran").get_data(as_text=True)
        self.assertIn('data-testid="waveform-plot"', body)
        for text in ("Time (ms)", "Vin (V)", "Vout (V)", "ms"):
            self.assertIn(text, body)

    def test_simulate_invalid_input_shows_error(self):
        body = post(self.client, sim_re="0").get_data(as_text=True)
        self.assertIn('data-testid="sim-error"', body)
        self.assertIn("re must be greater than zero", body)
        self.assertNotIn('data-testid="sim-result"', body)
        self.assertNotIn('data-testid="bode-plot"', body)
        self.assertNotIn('data-testid="waveform-plot"', body)

    def test_simulate_engine_error_shows_error(self):
        with patch.object(app_module, "run_analysis",
                          side_effect=NgspiceUnavailable("ngspice not found")):
            body = post(self.client).get_data(as_text=True)
        self.assertIn('data-testid="sim-error"', body)
        self.assertIn("ngspice not found", body)
        self.assertNotIn('data-testid="sim-result"', body)
        self.assertNotIn('data-testid="bode-plot"', body)

    def test_simulate_keeps_analytical_result_context(self):
        calc_body = self.client.post(
            "/calculate", data=REFERENCE_FORM).get_data(as_text=True)
        self.assertIn('data-testid="result-panel"', calc_body)
        analytical_fields = SIM_FORM.copy()
        analytical_fields.update(lab3_hidden_from(calc_body))

        with patch.object(app_module, "run_analysis", return_value=fixture_result("dc")):
            body = self.client.post(
                "/simulate", data=analytical_fields).get_data(as_text=True)
        self.assertIn('data-testid="result-panel"', body)
        self.assertIn("Analytical reference (Lab 3)", body)
        self.assertIn('name="bias_type"', body)
        self.assertIn("1.23 mA", body)
        self.assertIn("8.05 V", body)

    def test_simulate_error_keeps_analytical_result_context(self):
        calc_body = self.client.post(
            "/calculate", data=REFERENCE_FORM).get_data(as_text=True)
        analytical_fields = SIM_FORM.copy()
        analytical_fields.update(lab3_hidden_from(calc_body))
        with patch.object(app_module, "run_analysis",
                          side_effect=NgspiceUnavailable("ngspice not found")):
            body = self.client.post(
                "/simulate", data=analytical_fields).get_data(as_text=True)
        self.assertIn('data-testid="result-panel"', body)
        self.assertIn("1.23 mA", body)
        self.assertIn("8.05 V", body)

    def test_lab3_calculate_unchanged(self):
        resp = self.client.post("/calculate", data=REFERENCE_FORM)
        body = resp.get_data(as_text=True)
        self.assertIn("1.23 mA", body)
        self.assertIn("8.05 V", body)


if __name__ == "__main__":
    unittest.main()
