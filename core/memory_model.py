from dataclasses import dataclass

from .errors import OutOfRangeError, ReadOnlyError, TypeMismatchError


@dataclass(frozen=True)
class MemoryModel:
    device_suffix: str
    supported_spaces: tuple[str, ...]
    ranges: dict[str, dict[str, int]]
    scan_consistency_rule: str
    default_value: int
    writable: bool

    def validate(self, space: str, addr: int, count: int) -> None:
        if space not in self.supported_spaces:
            raise TypeMismatchError(f"{self.device_suffix} does not support {space}")
        if count < 1:
            raise OutOfRangeError("count must be >= 1")
        bounds = self.ranges.get(space)
        if not bounds:
            raise TypeMismatchError(f"{self.device_suffix} missing bounds for {space}")
        min_address = int(bounds["min_address"])
        max_address = int(bounds["max_address"])
        if addr < min_address or addr + count - 1 > max_address:
            raise OutOfRangeError(
                f"{self.device_suffix}/{space} [{addr}, {addr + count - 1}] out of range [{min_address}, {max_address}]"
            )

    def validate_writeable(self) -> None:
        if not self.writable:
            raise ReadOnlyError(f"{self.device_suffix} is read-only")
