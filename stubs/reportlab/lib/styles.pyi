from collections.abc import Mapping
from typing import Any

class ParagraphStyle:
    def __init__(self, name: str, parent: Any = ..., **kwargs: Any) -> None: ...

def getSampleStyleSheet() -> Mapping[str, Any]: ...
