import unittest
from pathlib import Path


IMAGES = Path(__file__).resolve().parents[1] / "docs" / "images"

DIAGRAMS = {
    "voltage-divider": ["VCC", "RC", "R1", "R2", "β", "VBE", "GND", "100 kΩ"],
    "fixed-bias": ["VCC", "RC", "RB", "β", "VBE", "GND", "1 MΩ"],
    "emitter-bias": ["VCC", "RC", "RB", "RE", "β", "VBE", "GND", "1 MΩ"],
}


class TestCircuitDiagrams(unittest.TestCase):
    def test_diagram_files_exist(self):
        for name in DIAGRAMS:
            for suffix in (".svg", ".png"):
                path = IMAGES / f"{name}{suffix}"
                self.assertTrue(path.is_file(), f"missing {path}")
                self.assertGreater(path.stat().st_size, 0, f"empty {path}")

    def test_svg_labels(self):
        for name, labels in DIAGRAMS.items():
            svg = (IMAGES / f"{name}.svg").read_text(encoding="utf-8")
            for label in labels:
                self.assertIn(label, svg, f"{name}.svg missing {label}")


if __name__ == "__main__":
    unittest.main()
