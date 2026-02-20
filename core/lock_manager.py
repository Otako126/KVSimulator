import threading

from .errors import LockTimeoutError


class LockManager:
    def __init__(self):
        self._locks: dict[str, threading.RLock] = {}
        self._meta_lock = threading.Lock()

    def _get_lock(self, dev: str) -> threading.RLock:
        with self._meta_lock:
            if dev not in self._locks:
                self._locks[dev] = threading.RLock()
            return self._locks[dev]

    def acquire(self, dev: str, timeout_ms: int):
        lock = self._get_lock(dev)
        ok = lock.acquire(timeout=timeout_ms / 1000)
        if not ok:
            raise LockTimeoutError(f"timeout acquiring lock for {dev}")
        return lock

    def release(self, dev: str) -> None:
        lock = self._get_lock(dev)
        lock.release()
