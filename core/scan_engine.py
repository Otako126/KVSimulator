import time
from dataclasses import dataclass

from .plc_parts import PlcParts
from .state_store import StateStore


@dataclass
class ScanConfig:
    mode: str = "real"
    period_ms: int = 10
    on_module_error: str = "CONTINUE"
    on_scan_error_wal: str = "DISCARD_WAL_FOR_SCAN"


class Hook:
    def on_scan_begin(self, ctx):
        return None

    def before_module(self, ctx, module):
        return None

    def after_module(self, ctx, module, outcome):
        return None

    def on_scan_end(self, ctx):
        return None


class ScanContext:
    def __init__(self, mem, state, plc, scan_id, delta_ms):
        self.mem = mem
        self.state = state
        self.plc = plc
        self.scan_id = scan_id
        self.delta_ms = delta_ms


class ScanEngine:
    def __init__(self, mem, modules, config: ScanConfig | None = None):
        self.mem = mem
        self.modules = modules
        self.config = config or ScanConfig()
        self.state = StateStore()
        self._hooks = []
        self._scan_id = 0
        self._last_time = time.time()
        self._delta_ms = self.config.period_ms
        self._plc = PlcParts(self.state, self._get_delta)

    def _get_delta(self):
        return self._delta_ms

    def register_hook(self, hook: Hook) -> None:
        self._hooks.append(hook)

    def _run_one(self):
        now = time.time()
        self._delta_ms = max(1, int((now - self._last_time) * 1000)) if self.config.mode != "step" else self.config.period_ms
        self._last_time = now
        self._scan_id += 1
        self.mem.begin_scan(self._scan_id, self._delta_ms)
        ctx = ScanContext(self.mem, self.state, self._plc, self._scan_id, self._delta_ms)
        for hook in self._hooks:
            hook.on_scan_begin(ctx)

        scan_failed = False
        for module in self.modules:
            for hook in self._hooks:
                hook.before_module(ctx, module)
            outcome = "ok"
            try:
                module.execute(ctx)
            except Exception:
                outcome = "error"
                scan_failed = True
                if self.config.on_module_error == "STOP":
                    raise
            finally:
                for hook in self._hooks:
                    hook.after_module(ctx, module, outcome)

        if scan_failed and self.config.on_scan_error_wal == "DISCARD_WAL_FOR_SCAN":
            self.mem.wal.discard_scan(self._scan_id)
        self.mem.apply_wal("scan_end", self._scan_id)
        for hook in self._hooks:
            hook.on_scan_end(ctx)
        self.mem.end_scan(self._scan_id)

    def step(self) -> None:
        self._run_one()

    def run_forever(self) -> None:
        while True:
            t0 = time.time()
            self._run_one()
            if self.config.mode == "real":
                elapsed = (time.time() - t0) * 1000
                wait_ms = max(0, self.config.period_ms - elapsed)
                time.sleep(wait_ms / 1000)
