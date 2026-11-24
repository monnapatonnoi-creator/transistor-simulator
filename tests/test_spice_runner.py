import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from spice_engine import (
    MODEL_NAME,
    NgspiceUnavailable,
    OutputEmpty,
    ParseFailed,
    RunFailed,
    SimInput,
    ngspice_version,
    run_analysis,
)

FIXTURES = Path(__file__).parent / "fixtures"
PARAMS = SimInput(
    vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0, re=1_000.0,
    rl=10_000.0, cin_f=10e-6, cout_f=10e-6, amplitude_v=0.010, freq_hz=1_000.0,
)


def fake_executable(folder: Path, body: str) -> str:
    script = folder / "fake.py"
    script.write_text(body, encoding="utf-8")
    cmd = folder / "fake.cmd"
    cmd.write_text(f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
    return str(cmd)


def writes_fixture(name: str) -> str:
    source = (FIXTURES / name).as_posix()
    return f"""import sys
from pathlib import Path
args = sys.argv[1:]
raw = Path(args[args.index('-r') + 1])
raw.write_text(Path({source!r}).read_text(encoding='utf-8'), encoding='utf-8')
"""


class RunnerFolder:
    """Keeps a temporary folder alive for the duration of one test."""

    def __init__(self, test: unittest.TestCase):
        self.tmp = tempfile.TemporaryDirectory()
        test.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)


class TestRunner(unittest.TestCase):
    def test_run_analysis_success_for_each_analysis(self):
        for analysis, fixture in (("dc", "lab4_dc.raw"), ("ac", "lab4_ac.raw"),
                                  ("tran", "lab4_tran.raw")):
            with self.subTest(analysis=analysis):
                folder = RunnerFolder(self)
                exe = fake_executable(folder.path, writes_fixture(fixture))
                result = run_analysis(PARAMS, analysis, exe=exe)
                self.assertEqual(result.status, "success")
                self.assertEqual(result.analysis, analysis)
                self.assertEqual(result.model, MODEL_NAME)
                self.assertIn(".end", result.netlist)
                self.assertIsNotNone(result.log_excerpt)
                if analysis == "dc":
                    self.assertGreater(result.op.ic, 0)
                elif analysis == "ac":
                    self.assertGreater(len(result.ac), 50)
                    self.assertIsNone(result.cutoff_hz)
                else:
                    self.assertGreater(len(result.tran), 200)

    def test_missing_engine(self):
        with self.assertRaises(NgspiceUnavailable):
            run_analysis(PARAMS, "dc", exe="Z:/definitely/not/here.exe")

    def test_failed_run(self):
        folder = RunnerFolder(self)
        exe = fake_executable(folder.path, "import sys\nsys.exit(1)\n")
        with self.assertRaises(RunFailed):
            run_analysis(PARAMS, "dc", exe=exe)

    def test_empty_output(self):
        folder = RunnerFolder(self)
        exe = fake_executable(
            folder.path,
            "import sys\nfrom pathlib import Path\n"
            "args = sys.argv[1:]\nPath(args[args.index('-r') + 1]).write_text('')\n",
        )
        with self.assertRaises(OutputEmpty):
            run_analysis(PARAMS, "dc", exe=exe)

    def test_timeout(self):
        folder = RunnerFolder(self)
        exe = fake_executable(folder.path, "import time\ntime.sleep(10)\n")
        with self.assertRaises(RunFailed):
            run_analysis(PARAMS, "dc", exe=exe, timeout=1.0)

    def test_unparseable_output(self):
        folder = RunnerFolder(self)
        exe = fake_executable(
            folder.path,
            "import sys\nfrom pathlib import Path\n"
            "args = sys.argv[1:]\nPath(args[args.index('-r') + 1]).write_text('garbage\\n')\n",
        )
        with self.assertRaises(ParseFailed):
            run_analysis(PARAMS, "dc", exe=exe)

    def test_subprocess_uses_list_and_cwd(self):
        folder = RunnerFolder(self)
        exe = fake_executable(folder.path, writes_fixture("lab4_dc.raw"))
        seen = {}

        def fake_run(args, **kwargs):
            seen["args"] = args
            seen["kwargs"] = kwargs
            seen["cwd_exists"] = Path(kwargs["cwd"]).is_dir()
            raw_path = Path(args[args.index("-r") + 1])
            raw_path.write_text((FIXTURES / "lab4_dc.raw").read_text(encoding="utf-8"),
                                encoding="utf-8")
            return subprocess.CompletedProcess(args, 0, "", "")

        with patch("spice_engine.subprocess.run", side_effect=fake_run):
            run_analysis(PARAMS, "dc", exe=exe)
        args = seen["args"]
        kwargs = seen["kwargs"]
        self.assertIsInstance(args, list)
        self.assertIn("-b", args)
        self.assertNotIn("shell", kwargs)
        self.assertIn("timeout", kwargs)
        self.assertTrue(seen["cwd_exists"])

    def test_ngspice_version_reads_raw_header(self):
        folder = RunnerFolder(self)
        exe = fake_executable(folder.path, writes_fixture("lab4_dc.raw"))
        self.assertIn("ngspice-47", ngspice_version(exe=exe))


if __name__ == "__main__":
    unittest.main()
