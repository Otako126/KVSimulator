from dataclasses import asdict, dataclass
import json
import time


@dataclass
class WalEntry:
    seq: int
    time_ms: int
    scan_id: int
    target_scan_id: int
    source: str
    dev: str
    space: str
    addr: int
    values: list[int]
    policy: str
    result: str = "accepted"


class WalStore:
    def __init__(self, max_entries: int = 100000):
        self.max_entries = max_entries
        self._seq = 0
        self._entries: list[WalEntry] = []

    def append(self, entry: WalEntry) -> int:
        self._seq += 1
        entry.seq = self._seq
        if entry.time_ms == 0:
            entry.time_ms = int(time.time() * 1000)
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries :]
        return entry.seq

    def iter_ready(self, scan_id: int):
        for entry in self._entries:
            if entry.target_scan_id <= scan_id:
                yield entry

    def discard_scan(self, scan_id: int, source_prefix: str = "ladder:") -> None:
        self._entries = [
            e for e in self._entries if not (e.scan_id == scan_id and e.source.startswith(source_prefix))
        ]

    def remove_applied(self, scan_id: int) -> None:
        self._entries = [e for e in self._entries if e.target_scan_id > scan_id]


    def size(self) -> int:
        return len(self._entries)

    def to_ndjson(self) -> str:
        return "\n".join(json.dumps(asdict(e), ensure_ascii=False) for e in self._entries)
