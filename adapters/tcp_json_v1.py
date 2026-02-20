import json
import socket
import threading
import time

from core.errors import SimError, TooManyPointsError
from .schema import SchemaValidator


class TcpJsonV1Server:
    def __init__(self, device_memory, name: str, bind_ip: str, port: int, limits: dict | None = None, readonly: bool = False):
        self.device_memory = device_memory
        self.name = name
        self.bind_ip = bind_ip
        self.port = port
        self.readonly = readonly
        self.limits = limits or {"max_points_per_request": 1024, "max_frame_bytes": 1024 * 1024}
        self.validator = SchemaValidator()
        self._server = None
        self._running = False

    def start(self):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((self.bind_ip, self.port))
        self._server.listen()
        self._running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def stop(self):
        self._running = False
        if self._server:
            self._server.close()

    def _accept_loop(self):
        while self._running:
            try:
                client, _ = self._server.accept()
            except OSError:
                break
            threading.Thread(target=self.handle_client, args=(client,), daemon=True).start()

    def _dispatch_read(self, req):
        count = req["count"]
        if count > self.limits["max_points_per_request"]:
            raise TooManyPointsError("count over limit")
        if req["space"] == "bit":
            values = self.device_memory.read_bits(req["dev"], req["addr"], count, source=f"adapter:{self.name}")
        elif req["space"] == "word":
            values = self.device_memory.read_words(req["dev"], req["addr"], count, source=f"adapter:{self.name}")
        else:
            values = self.device_memory.read_dwords(req["dev"], req["addr"], count, source=f"adapter:{self.name}")
        return {"ok": True, "values": values, "diag": {"scan": self.device_memory.current_scan_id}}

    def _dispatch_write(self, req):
        values = req["values"]
        if len(values) > self.limits["max_points_per_request"]:
            raise TooManyPointsError("values over limit")
        if self.readonly:
            raise SimError("adapter in readonly mode")
        if req["space"] == "bit":
            self.device_memory.write_bits(req["dev"], req["addr"], values, source=f"adapter:{self.name}")
        elif req["space"] == "word":
            self.device_memory.write_words(req["dev"], req["addr"], values, source=f"adapter:{self.name}")
        else:
            self.device_memory.write_dwords(req["dev"], req["addr"], values, source=f"adapter:{self.name}")
        return {"ok": True, "diag": {"scan": self.device_memory.current_scan_id, "time_ms": int(time.time() * 1000)}}

    def handle_client(self, conn: socket.socket):
        with conn:
            buffer = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if len(line) > self.limits["max_frame_bytes"]:
                        out = {"ok": False, "err": {"code": "INVALID_REQUEST", "message": "frame too large"}}
                    else:
                        out = self._handle_line(line)
                    conn.sendall((json.dumps(out, ensure_ascii=False) + "\n").encode("utf-8"))

    def _handle_line(self, line: bytes):
        try:
            req = json.loads(line.decode("utf-8"))
            self.validator.validate_request(req)
            if req["op"] == "read":
                return self._dispatch_read(req)
            return self._dispatch_write(req)
        except SimError as exc:
            return {"ok": False, "err": {"code": exc.code, "message": exc.message, "detail": exc.detail}}
        except Exception as exc:
            return {"ok": False, "err": {"code": "INTERNAL_ERROR", "message": str(exc)}}
