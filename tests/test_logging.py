import json
import tempfile
import unittest
from pathlib import Path

from core.device_memory import DeviceMemory, DeviceMemoryOptions
from core.scan_engine import ScanConfig, ScanEngine
from core.sim_logger import NullLogger, build_scan_logger
from core.wal import WalStore
from modules.base import LadderModuleBase
from profiles.profile_loader import DeviceProfileLoader


class NoopModule(LadderModuleBase):
    name = "Noop"

    def execute(self, ctx):
        return None


class LoggingTests(unittest.TestCase):
    def setUp(self):
        profile = DeviceProfileLoader.load("profiles/kv8000.yaml")
        self.mem = DeviceMemory(profile, WalStore(), DeviceMemoryOptions())

    def test_debug_off_uses_null_logger(self):
        logger = build_scan_logger({"log_level": "INFO"}, {"file_path": "logs/x.log", "max_bytes": 100, "backup_count": 1})
        self.assertIsInstance(logger, NullLogger)

    def test_debug_on_writes_and_rotates(self):
        with tempfile.TemporaryDirectory() as d:
            log_path = Path(d) / "scan.log"
            logger = build_scan_logger(
                {"log_level": "DEBUG"},
                {"file_path": str(log_path), "max_bytes": 180, "backup_count": 2},
            )
            engine = ScanEngine(self.mem, [NoopModule()], ScanConfig(mode="step", period_ms=10), logger=logger)
            for _ in range(30):
                engine.step()

            files = sorted(log_path.parent.glob("scan.log*"))
            self.assertTrue(any(f.name == "scan.log" for f in files))
            # RotatingFileHandler keeps active + backup_count files at most.
            self.assertLessEqual(len(files), 3)
            self.assertTrue(any("scan_begin" in f.read_text(encoding="utf-8") for f in files if f.exists()))


if __name__ == "__main__":
    unittest.main()
