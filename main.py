import importlib
import json
from pathlib import Path

from adapters.tcp_json_v1 import TcpJsonV1Server
from core.device_memory import DeviceMemory, DeviceMemoryOptions
from core.scan_engine import ScanConfig, ScanEngine
from core.sim_logger import build_scan_logger
from core.wal import WalStore
from profiles.profile_loader import DeviceProfileLoader


def load_simulator_config(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_app(config_path: str = "simulator.yaml"):
    cfg = load_simulator_config(config_path)
    profile = DeviceProfileLoader.load(cfg["profile"]["path"])
    mem = DeviceMemory(
        profile,
        WalStore(max_entries=cfg["wal"]["max_entries"]),
        DeviceMemoryOptions(
            lock_timeout_ms=cfg["locks"]["timeout_ms"],
            read_your_writes=cfg["consistency"]["read_your_writes"],
            apply_phase=cfg["consistency"]["apply_phase"],
        ),
    )
    modules = []
    for module_name in cfg["modules"]:
        mod = importlib.import_module(f"modules.{module_name}")
        modules.append(mod.Module())
    scan_logger = build_scan_logger(cfg.get("simulator", {}), cfg.get("logging", {}))
    engine = ScanEngine(
        mem,
        modules,
        ScanConfig(
            mode=cfg["scan"]["mode"],
            period_ms=cfg["scan"]["period_ms"],
            on_module_error=cfg["scan"]["on_module_error"],
            on_scan_error_wal=cfg["scan"]["on_scan_error_wal"],
        ),
        logger=scan_logger,
    )
    adapters = []
    for a in cfg["adapters"]:
        adapters.append(
            TcpJsonV1Server(
                mem,
                name=a["name"],
                bind_ip=a["bind_ip"],
                port=a["port"],
                limits=a["limits"],
                readonly=a["readonly"],
            )
        )
    return engine, adapters


def main():
    engine, adapters = build_app()
    for a in adapters:
        a.start()
    if engine.config.mode == "step":
        engine.step()
    else:
        engine.run_forever()


if __name__ == "__main__":
    main()
