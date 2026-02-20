"""KVSimulator sample program.

This script demonstrates a tiny end-to-end flow without opening sockets:
1. build simulator objects from `simulator.yaml`
2. write input relay R0 from an external source (adapter equivalent)
3. run scan cycles in `step` mode
4. read resulting MR/DM values
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import build_app


def dump(mem, label: str) -> None:
    print(f"\n{label}")
    print("R0:", mem.read_bits("R", 0, 1, source="adapter:example"))
    print("MR0, MR1:", mem.read_bits("MR", 0, 2, source="adapter:example"))
    print("DM100, DM101:", mem.read_words("DM", 100, 2, source="adapter:example"))


def main() -> None:
    engine, _ = build_app("simulator.yaml")
    mem = engine.mem

    dump(mem, "== Initial ==")

    print("\nWrite R0=1 (external)")
    mem.write_bits("R", 0, [1], source="adapter:example")

    for i in range(1, 5):
        engine.step()
        dump(mem, f"After scan #{i}")


if __name__ == "__main__":
    main()
