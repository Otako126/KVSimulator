from .state_store import StateStore


class PlcParts:
    def __init__(self, state: StateStore, delta_provider):
        self.state = state
        self.delta_provider = delta_provider

    def edge_rise(self, id: str, signal: bool) -> bool:
        key = f"edge:rise:{id}"
        prev = bool(self.state.get(key, False))
        self.state.set(key, bool(signal))
        return (not prev) and bool(signal)

    def edge_fall(self, id: str, signal: bool) -> bool:
        key = f"edge:fall:{id}"
        prev = bool(self.state.get(key, False))
        self.state.set(key, bool(signal))
        return prev and (not bool(signal))

    def ton(self, id: str, in_signal: bool, pt_ms: int) -> bool:
        key = f"ton:{id}:et"
        et = int(self.state.get(key, 0))
        if in_signal:
            et += self.delta_provider()
            self.state.set(key, et)
            return et >= pt_ms
        self.state.set(key, 0)
        return False

    def tof(self, id: str, in_signal: bool, pt_ms: int) -> bool:
        key = f"tof:{id}:et"
        if in_signal:
            self.state.set(key, 0)
            return True
        et = int(self.state.get(key, 0)) + self.delta_provider()
        self.state.set(key, et)
        return et < pt_ms

    def tp(self, id: str, in_signal: bool, pt_ms: int) -> bool:
        rise = self.edge_rise(f"tp:{id}:rise", in_signal)
        running_key = f"tp:{id}:running"
        et_key = f"tp:{id}:et"
        running = bool(self.state.get(running_key, False))
        et = int(self.state.get(et_key, 0))
        if rise:
            running = True
            et = 0
        if running:
            et += self.delta_provider()
            if et >= pt_ms:
                running = False
        self.state.set(running_key, running)
        self.state.set(et_key, et)
        return running

    def ctu(self, id: str, in_signal: bool, pv: int, *, reset: bool = False) -> tuple[bool, int]:
        cv_key = f"ctu:{id}:cv"
        cv = int(self.state.get(cv_key, 0))
        if reset:
            cv = 0
        if self.edge_rise(f"ctu:{id}:edge", in_signal):
            cv += 1
        self.state.set(cv_key, cv)
        return cv >= pv, cv

    def ctd(self, id: str, in_signal: bool, pv: int, *, reset: bool = False) -> tuple[bool, int]:
        cv_key = f"ctd:{id}:cv"
        cv = int(self.state.get(cv_key, pv))
        if reset:
            cv = pv
        if self.edge_rise(f"ctd:{id}:edge", in_signal):
            cv -= 1
        self.state.set(cv_key, cv)
        return cv <= 0, cv
