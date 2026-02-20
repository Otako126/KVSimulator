from collections import defaultdict
from dataclasses import dataclass
from threading import Lock

from .device_profile import DeviceProfile
from .errors import OutOfRangeError
from .lock_manager import LockManager
from .wal import WalEntry, WalStore


@dataclass
class DeviceMemoryOptions:
    lock_timeout_ms: int = 5000
    read_your_writes: bool = False
    apply_phase: str = "scan_end"


class DeviceMemory:
    def __init__(self, profile: DeviceProfile, wal: WalStore, options: DeviceMemoryOptions | None = None):
        self.profile = profile
        self.wal = wal
        self.options = options or DeviceMemoryOptions()
        self.locks = LockManager()
        self.current_scan_id = 0
        self.current_delta_ms = 0
        self._cs = defaultdict(dict)  # (dev,space)->addr->value
        self._image = defaultdict(dict)
        self._scan_lock = Lock()

    def begin_scan(self, scan_id: int, delta_ms: int) -> None:
        with self._scan_lock:
            self.current_scan_id = scan_id
            self.current_delta_ms = delta_ms
            self._image = defaultdict(dict)
            for dev, model in self.profile.devices.items():
                if model.scan_consistency_rule == "IO_IMAGE":
                    for space in model.supported_spaces:
                        self._image[(dev, space)] = dict(self._cs[(dev, space)])

    def end_scan(self, scan_id: int) -> None:
        self.current_scan_id = scan_id

    def apply_wal(self, phase: str, scan_id: int) -> None:
        if phase != self.options.apply_phase:
            return
        pending = sorted(self.wal.iter_ready(scan_id), key=lambda e: e.seq)
        for entry in pending:
            self._write_cs(entry.dev, entry.space, entry.addr, entry.values)
        self.wal.remove_applied(scan_id)

    def _resolve_reads(self, dev: str, space: str, source: str) -> dict[int, int]:
        model = self.profile.get_model(dev)
        if source.startswith("ladder") and model.scan_consistency_rule == "IO_IMAGE":
            return self._image[(dev, space)]
        return self._cs[(dev, space)]

    def _read(self, dev: str, space: str, addr: int, count: int, *, source: str) -> list[int]:
        model = self.profile.get_model(dev)
        model.validate(space, addr, count)
        data = self._resolve_reads(dev, space, source)
        return [int(data.get(i, model.default_value)) for i in range(addr, addr + count)]

    def _write_cs(self, dev: str, space: str, addr: int, values: list[int]) -> None:
        model = self.profile.get_model(dev)
        store = self._cs[(dev, space)]
        for i, val in enumerate(values):
            if space == "bit" and val not in (0, 1, True, False):
                raise OutOfRangeError("bit value must be 0/1")
            if space == "word" and not (0 <= int(val) <= 65535):
                raise OutOfRangeError("word value must be 0..65535")
            if space == "dword" and not (0 <= int(val) <= (2**32 - 1)):
                raise OutOfRangeError("dword value must be 0..2^32-1")
            store[addr + i] = int(val)

    def _write(self, dev: str, space: str, addr: int, values: list[int], *, source: str) -> None:
        model = self.profile.get_model(dev)
        model.validate(space, addr, len(values))
        model.validate_writeable()
        lock = self.locks.acquire(dev, self.options.lock_timeout_ms)
        try:
            policy = model.scan_consistency_rule
            if policy == "IMMEDIATE":
                self._write_cs(dev, space, addr, values)
            elif policy in ("NEXT_SCAN", "IO_IMAGE"):
                self.wal.append(
                    WalEntry(
                        seq=0,
                        time_ms=0,
                        scan_id=self.current_scan_id,
                        target_scan_id=self.current_scan_id + 1,
                        source=source,
                        dev=dev,
                        space=space,
                        addr=addr,
                        values=[int(v) for v in values],
                        policy=policy,
                    )
                )
            else:
                raise OutOfRangeError(f"unsupported policy {policy}")
        finally:
            lock.release()

    def read_bits(self, dev: str, addr: int, count: int, *, source: str) -> list[int]:
        return self._read(dev, "bit", addr, count, source=source)

    def write_bits(self, dev: str, addr: int, values: list[int], *, source: str) -> None:
        self._write(dev, "bit", addr, values, source=source)

    def read_words(self, dev: str, addr: int, count: int, *, source: str) -> list[int]:
        return self._read(dev, "word", addr, count, source=source)

    def write_words(self, dev: str, addr: int, values: list[int], *, source: str) -> None:
        self._write(dev, "word", addr, values, source=source)

    def read_dwords(self, dev: str, addr: int, count: int, *, source: str) -> list[int]:
        return self._read(dev, "dword", addr, count, source=source)

    def write_dwords(self, dev: str, addr: int, values: list[int], *, source: str) -> None:
        self._write(dev, "dword", addr, values, source=source)
