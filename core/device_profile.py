from dataclasses import dataclass

from .errors import UnknownDeviceError
from .memory_model import MemoryModel


@dataclass
class DeviceProfile:
    name: str
    version: int
    description: str
    devices: dict[str, MemoryModel]

    def get_model(self, dev: str) -> MemoryModel:
        try:
            return self.devices[dev]
        except KeyError as exc:
            raise UnknownDeviceError(f"Unknown device: {dev}") from exc
