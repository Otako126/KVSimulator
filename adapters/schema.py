from core.errors import InvalidRequestError


class SchemaValidator:
    SPACES = {"bit", "word", "dword"}

    def validate_request(self, obj):
        if not isinstance(obj, dict):
            raise InvalidRequestError("request must be object")
        op = obj.get("op")
        if op not in {"read", "write"}:
            raise InvalidRequestError("op must be read/write")
        if obj.get("space") not in self.SPACES:
            raise InvalidRequestError("space must be bit/word/dword")
        if not isinstance(obj.get("dev"), str) or not obj["dev"]:
            raise InvalidRequestError("dev required")
        if not isinstance(obj.get("addr"), int) or obj["addr"] < 0:
            raise InvalidRequestError("addr must be >=0")
        if op == "read":
            if set(obj.keys()) - {"id", "op", "space", "dev", "addr", "count"}:
                raise InvalidRequestError("additional properties are not allowed")
            if not isinstance(obj.get("count"), int) or obj["count"] < 1:
                raise InvalidRequestError("count must be >=1")
        else:
            if set(obj.keys()) - {"id", "op", "space", "dev", "addr", "values"}:
                raise InvalidRequestError("additional properties are not allowed")
            values = obj.get("values")
            if not isinstance(values, list) or not values:
                raise InvalidRequestError("values must be non-empty array")

    def validate_response(self, obj):
        if not isinstance(obj, dict) or "ok" not in obj:
            raise InvalidRequestError("response must include ok")
