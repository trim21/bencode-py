from typing import Any

from typing_extensions import Buffer

def bdecode(b: Buffer, /) -> Any: ...
def bencode(v: Any, /) -> bytes: ...

class BencodeDecodeError(ValueError): ...
class BencodeEncodeError(ValueError): ...