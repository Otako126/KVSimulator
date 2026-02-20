class StateStore:
    def __init__(self):
        self._state = {}

    def get(self, key, default=None):
        return self._state.get(key, default)

    def set(self, key, val):
        self._state[key] = val

    def reset_scope(self, prefix: str):
        keys = [k for k in self._state if str(k).startswith(prefix)]
        for key in keys:
            del self._state[key]
