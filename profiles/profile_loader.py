import json
from pathlib import Path

from core.device_profile import DeviceProfile
from core.memory_model import MemoryModel


class DeviceProfileLoader:
    @staticmethod
    def load(path: str) -> DeviceProfile:
        raw = Path(path).read_text(encoding="utf-8")
        data = json.loads(raw)
        profile = data["profile"]
        devices = {}
        for item in data["devices"]:
            model = MemoryModel(
                device_suffix=item["device_suffix"],
                supported_spaces=tuple(item["supported_spaces"]),
                ranges=item["ranges"],
                scan_consistency_rule=item["scan_consistency_rule"],
                default_value=int(item.get("default_value", 0)),
                writable=bool(item.get("writable", True)),
            )
            devices[model.device_suffix] = model
        return DeviceProfile(
            name=profile["name"],
            version=int(profile["version"]),
            description=profile.get("description", ""),
            devices=devices,
        )
