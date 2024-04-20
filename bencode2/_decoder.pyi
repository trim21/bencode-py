from typing import Any

class Decoder:
    str_key: bool

    def __init__(self, str_key: bool): ...
    def decode(self, value: bytes) -> Any: ...
