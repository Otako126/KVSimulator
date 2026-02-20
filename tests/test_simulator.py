import unittest

from core.device_memory import DeviceMemory, DeviceMemoryOptions
from core.scan_engine import ScanConfig, ScanEngine
from core.wal import WalStore
from modules.base import LadderModuleBase
from profiles.profile_loader import DeviceProfileLoader


class DummyModule(LadderModuleBase):
    name = "D"

    def execute(self, ctx):
        ctx.mem.write_bits("MR", 10, [1], source="ladder:D")


class FailingModule(LadderModuleBase):
    name = "F"

    def execute(self, ctx):
        ctx.mem.write_bits("MR", 11, [1], source="ladder:F")
        raise RuntimeError("boom")


class SimulatorTests(unittest.TestCase):
    def setUp(self):
        profile = DeviceProfileLoader.load("profiles/kv8000.yaml")
        self.mem = DeviceMemory(profile, WalStore(), DeviceMemoryOptions())

    def test_sparse_default_read(self):
        self.assertEqual(self.mem.read_words("DM", 0, 2, source="adapter:test"), [0, 0])

    def test_range_boundary(self):
        self.mem.write_words("DM", 65534, [1], source="adapter:test")
        self.assertEqual(self.mem.read_words("DM", 65534, 1, source="adapter:test"), [1])
        with self.assertRaises(Exception):
            self.mem.read_words("DM", 65535, 1, source="adapter:test")

    def test_next_scan_reflect(self):
        self.mem.begin_scan(1, 10)
        self.mem.write_bits("MR", 0, [1], source="adapter:test")
        self.assertEqual(self.mem.read_bits("MR", 0, 1, source="adapter:test"), [0])
        self.mem.apply_wal("scan_end", 2)
        self.assertEqual(self.mem.read_bits("MR", 0, 1, source="adapter:test"), [1])

    def test_io_image_freeze(self):
        self.mem.begin_scan(1, 10)
        self.mem.write_bits("R", 0, [1], source="adapter:test")
        self.assertEqual(self.mem.read_bits("R", 0, 1, source="ladder:A"), [0])
        self.mem.apply_wal("scan_end", 2)
        self.assertEqual(self.mem.read_bits("R", 0, 1, source="adapter:test"), [1])

    def test_scan_error_discards_ladder_wal(self):
        engine = ScanEngine(
            self.mem,
            [FailingModule()],
            ScanConfig(mode="step", on_module_error="CONTINUE", on_scan_error_wal="DISCARD_WAL_FOR_SCAN"),
        )
        engine.step()
        self.assertEqual(self.mem.read_bits("MR", 11, 1, source="adapter:test"), [0])

    def test_plc_parts_ctu(self):
        engine = ScanEngine(self.mem, [DummyModule()], ScanConfig(mode="step", period_ms=10))
        engine.step()
        engine.step()
        # one-shot on rising edge in module: writes same bit again, but still should be committed once
        self.assertEqual(self.mem.read_bits("MR", 10, 1, source="adapter:test"), [1])


if __name__ == "__main__":
    unittest.main()
