import unittest

from app import DEFAULTS, create_app
from dc_bias import BIAS_REGISTRY


class TestIndexPage(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_get_index_returns_form(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe", "bias_type"):
            self.assertIn(f'name="{field}"', body)
        self.assertNotIn('data-testid="result-panel"', body)

    def test_defaults_prefilled_in_kohm(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('value="12"', body)
        self.assertIn('value="100"', body)
        self.assertIn('value="22"', body)
        self.assertIn('value="2.2"', body)
        self.assertIn('value="0.70"', body)
        self.assertIn('<option value="kohm" selected', body)

    def test_bias_options_come_from_registry(self):
        body = self.client.get("/").get_data(as_text=True)
        for key in BIAS_REGISTRY:
            self.assertIn(f'<option value="{key}"', body)

    def test_stylesheet_is_linked(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("/static/style.css", body)


REFERENCE_FORM = {
    "bias_type": "voltage_divider", "vcc": "12",
    "r1": "100", "r1_unit": "kohm", "r2": "22", "r2_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm", "re": "1", "re_unit": "kohm",
    "beta": "100", "vbe": "0.70",
}


class TestCalculate(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_reference_case_renders_backend_values(self):
        resp = self.client.post("/calculate", data=REFERENCE_FORM)
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn('data-testid="result-panel"', body)
        self.assertIn("8.05 V", body)
        self.assertIn("1.23 mA", body)
        self.assertIn("12.3 µA", body)
        self.assertIn("18.0 kΩ", body)
        self.assertIn("Forward Active", body)

    def test_beta_changes_result(self):
        form = dict(REFERENCE_FORM, beta="50")
        body = self.client.post("/calculate", data=form).get_data(as_text=True)
        self.assertIn("1.06 mA", body)
        self.assertNotIn("1.23 mA", body)


if __name__ == "__main__":
    unittest.main()
