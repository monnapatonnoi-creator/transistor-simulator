import re
import unittest

from app import DEFAULTS, _to_ohms, create_app
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


class TestValidationWeb(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_zero_beta_shows_error(self):
        resp = self.client.post("/calculate", data=dict(REFERENCE_FORM, beta="0"))
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn('data-testid="error-block"', body)
        self.assertIn("beta must be greater than zero", body)
        self.assertNotIn('data-testid="result-panel"', body)

    def test_non_numeric_vcc_shows_error(self):
        resp = self.client.post("/calculate", data=dict(REFERENCE_FORM, vcc="abc"))
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn("vcc must be a number", body)

    def test_whitespace_input_shows_error(self):
        resp = self.client.post("/calculate", data=dict(REFERENCE_FORM, vcc="   "))
        body = resp.get_data(as_text=True)
        self.assertIn("vcc must be a number", body)

    def test_unknown_unit_shows_error(self):
        resp = self.client.post("/calculate", data=dict(REFERENCE_FORM, r1_unit="mega"))
        body = resp.get_data(as_text=True)
        self.assertIn("Unknown unit: mega", body)

    def test_unknown_bias_type_shows_error(self):
        resp = self.client.post("/calculate", data=dict(REFERENCE_FORM, bias_type="no_such_bias"))
        body = resp.get_data(as_text=True)
        self.assertIn("Unknown bias type: no_such_bias", body)

    def test_submitted_values_preserved(self):
        body = self.client.post("/calculate", data=dict(REFERENCE_FORM, beta="0", r1="47")).get_data(as_text=True)
        self.assertIn('value="47"', body)


class TestRegionPresentation(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_cutoff_shows_warning_and_caveat(self):
        body = self.client.post("/calculate", data=dict(REFERENCE_FORM, vcc="5", r2="5")).get_data(as_text=True)
        self.assertIn("Cutoff", body)
        self.assertIn('data-testid="warning-block"', body)
        self.assertIn("do not apply", body)
        self.assertIn('data-testid="model-caveat"', body)
        self.assertIn("is-invalid", body)

    def test_saturation_shows_warning(self):
        body = self.client.post("/calculate", data=dict(REFERENCE_FORM, rc="10")).get_data(as_text=True)
        self.assertIn("Saturation", body)
        self.assertIn('data-testid="warning-block"', body)

    def test_active_has_no_warning_or_caveat(self):
        body = self.client.post("/calculate", data=REFERENCE_FORM).get_data(as_text=True)
        self.assertNotIn('data-testid="warning-block"', body)
        self.assertNotIn('data-testid="model-caveat"', body)
        self.assertNotIn("is-invalid", body)


class TestModeSwitch(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_get_default_still_shows_all_divider_fields(self):
        body = self.client.get("/").get_data(as_text=True)
        for field in ("r1", "r2", "re"):
            self.assertIn(f'name="{field}"', body)
        self.assertNotIn('name="rb"', body)

    def test_get_fixed_mode_hides_r1_and_re(self):
        body = self.client.get("/?bias_type=fixed_bias").get_data(as_text=True)
        self.assertIn('name="rb"', body)
        for field in ("r1", "r2", "re"):
            self.assertNotIn(f'name="{field}"', body)
        self.assertIn('<option value="fixed_bias" selected', body)

    def test_get_emitter_mode_hides_r1_r2(self):
        body = self.client.get("/?bias_type=emitter_bias").get_data(as_text=True)
        self.assertIn('name="rb"', body)
        self.assertIn('name="re"', body)
        self.assertNotIn('name="r1"', body)
        self.assertNotIn('name="r2"', body)

    def test_mode_switch_preserves_typed_values(self):
        body = self.client.get(
            "/?bias_type=fixed_bias&vcc=9&rb=470&rb_unit=kohm"
            "&rc=1.5&rc_unit=kohm&beta=80&vbe=0.65"
        ).get_data(as_text=True)
        for value in ("9", "470", "1.5", "80", "0.65"):
            self.assertIn(f'value="{value}"', body)

    def test_values_survive_round_trip_through_hidden_mode(self):
        # Divider R1=47, switch to Fixed (R1 hidden), then back to Divider.
        fixed = self.client.get(
            "/?bias_type=fixed_bias&vcc=12&beta=100&vbe=0.70"
            "&rb=1000&rb_unit=kohm&rc=2.2&rc_unit=kohm"
            "&r1=47&r1_unit=kohm&r2=22&r2_unit=kohm&re=1&re_unit=kohm"
        ).get_data(as_text=True)
        self.assertIn('name="carry_r1" value="47"', fixed)
        self.assertIn('name="carry_r1_unit" value="kohm"', fixed)

        back = self.client.get(
            "/?bias_type=voltage_divider&vcc=12&beta=100&vbe=0.70"
            "&rb=1000&rb_unit=kohm&rc=2.2&rc_unit=kohm"
            "&carry_r1=47&carry_r1_unit=kohm"
            "&carry_r2=22&carry_r2_unit=kohm"
            "&carry_re=1&carry_re_unit=kohm"
        ).get_data(as_text=True)
        self.assertIn('name="r1" step="any" value="47"', back)


FIXED_FORM = {
    "bias_type": "fixed_bias", "vcc": "12",
    "rb": "1000", "rb_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm",
    "beta": "100", "vbe": "0.70",
}
EMITTER_FORM = dict(FIXED_FORM, bias_type="emitter_bias", re="1", re_unit="kohm")


class TestLab03Cases(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_fixed_reference_case(self):
        resp = self.client.post("/calculate", data=FIXED_FORM)
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn("1.13 mA", body)
        self.assertIn("9.51 V", body)
        self.assertIn("Mode: fixed_bias", body)

    def test_emitter_reference_case(self):
        body = self.client.post("/calculate", data=EMITTER_FORM).get_data(as_text=True)
        self.assertIn("1.03 mA", body)
        self.assertIn("8.71 V", body)

    def test_emitter_re_change_affects_result(self):
        body = self.client.post(
            "/calculate", data=dict(EMITTER_FORM, re="2")
        ).get_data(as_text=True)
        self.assertNotIn("1.03 mA", body)
        # 0.9401 mA is rendered by the shared Lab 02 formatter as 940 µA.
        self.assertIn("940 µA", body)

    def test_fixed_zero_rb_shows_error(self):
        resp = self.client.post("/calculate", data=dict(FIXED_FORM, rb="0"))
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn("rb must be greater than zero", body)
        self.assertNotIn('data-testid="result-panel"', body)

    def test_fixed_missing_rb_shows_error(self):
        data = {k: v for k, v in FIXED_FORM.items() if k != "rb"}
        body = self.client.post("/calculate", data=data).get_data(as_text=True)
        self.assertIn("rb must be a number", body)

    def test_unknown_mode_shows_error(self):
        body = self.client.post(
            "/calculate", data=dict(FIXED_FORM, bias_type="no_such_bias")
        ).get_data(as_text=True)
        self.assertIn("Unknown bias type: no_such_bias", body)

    def test_non_finite_input_shows_error_not_500(self):
        for field in ("vcc", "beta", "vbe", "rb"):
            with self.subTest(field=field):
                resp = self.client.post(
                    "/calculate", data=dict(FIXED_FORM, **{field: "nan"})
                )
                body = resp.get_data(as_text=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn(f"{field} must be a finite number", body)
                self.assertNotIn('data-testid="result-panel"', body)
        resp = self.client.post("/calculate", data=dict(FIXED_FORM, rb="1e309"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("rb must be a finite number", resp.get_data(as_text=True))

    def test_divider_unchanged(self):
        body = self.client.post("/calculate", data=REFERENCE_FORM).get_data(as_text=True)
        self.assertIn("8.05 V", body)
        self.assertIn("1.23 mA", body)
        self.assertIn("18.0 kΩ", body)


class TestMegaohmUnit(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_mohm_conversion(self):
        self.assertEqual(_to_ohms("1", "mohm"), 1e6)
        self.assertEqual(_to_ohms("2.2", "mohm"), 2.2e6)

    def test_mohm_option_in_every_resistor_field(self):
        fields_by_mode = {
            "/": ["r1", "r2", "rc", "re"],
            "/?bias_type=fixed_bias": ["rb", "rc"],
            "/?bias_type=emitter_bias": ["rb", "rc", "re"],
        }
        for url, fields in fields_by_mode.items():
            body = self.client.get(url).get_data(as_text=True)
            for field in fields:
                select = re.search(
                    rf'<select name="{field}_unit">.*?</select>', body, re.S
                )
                self.assertIsNotNone(select, f"{url}: {field}_unit dropdown missing")
                self.assertIn(
                    '<option value="mohm">MΩ</option>',
                    select.group(0),
                    f"{url}: {field}_unit missing MΩ",
                )

    def test_mohm_rb_reproduces_a2(self):
        body = self.client.post(
            "/calculate", data=dict(FIXED_FORM, rb="1", rb_unit="mohm")
        ).get_data(as_text=True)
        self.assertIn("1.13 mA", body)
        self.assertIn("9.51 V", body)

    def test_mohm_unit_survives_mode_switch(self):
        fixed = self.client.get(
            "/?bias_type=fixed_bias&rb=1&rb_unit=mohm"
        ).get_data(as_text=True)
        self.assertIn('name="rb_unit" value="mohm"', fixed)
        back = self.client.get(
            "/?bias_type=voltage_divider&carry_rb_unit=mohm"
        ).get_data(as_text=True)
        self.assertIn('name="carry_rb_unit" value="mohm"', back)


class TestLiveDiagram(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def _group_class(self, body: str, group: str) -> str:
        match = re.search(rf'<g data-group="{group}" class="([^"]*)"', body)
        self.assertIsNotNone(match, f"missing diagram group {group}")
        return match.group(1)

    def test_diagram_is_rendered_with_current_values(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('class="live-diagram"', body)
        self.assertIn('data-bind="vcc">12 V', body)
        self.assertIn('data-bind="r1">100 kΩ', body)
        self.assertIn('data-bind="beta">100', body)

    def test_diagram_uses_megaohm_label(self):
        body = self.client.get(
            "/?bias_type=fixed_bias&rb=1&rb_unit=mohm"
        ).get_data(as_text=True)
        self.assertIn('data-bind="rb">1 MΩ', body)

    def test_diagram_groups_follow_bias_mode(self):
        cases = {
            "/": {
                "r1": False, "r2": False, "rb": True,
                "re": False, "emitter-direct": True,
            },
            "/?bias_type=fixed_bias": {
                "r1": True, "r2": True, "rb": False,
                "re": True, "emitter-direct": False,
            },
            "/?bias_type=emitter_bias": {
                "r1": True, "r2": True, "rb": False,
                "re": False, "emitter-direct": True,
            },
        }
        for url, expected in cases.items():
            body = self.client.get(url).get_data(as_text=True)
            for group, hidden in expected.items():
                self.assertEqual(
                    "is-hidden" in self._group_class(body, group),
                    hidden,
                    f"{url}: wrong visibility for {group}",
                )

    def test_diagram_result_values(self):
        body = self.client.post(
            "/calculate", data=REFERENCE_FORM
        ).get_data(as_text=True)
        self.assertIn('data-bind="ic">1.23 mA', body)
        self.assertIn('data-bind="vce">8.05 V', body)


if __name__ == "__main__":
    unittest.main()
