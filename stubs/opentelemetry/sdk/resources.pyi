from typing import Any

class Resource:
    @classmethod
    def create(cls, attributes: dict[str, Any]) -> Resource: ...
