from __future__ import annotations

from io import StringIO
from tokenize import TokenInfo, generate_tokens


def collect_tokens(source_text: str) -> tuple[TokenInfo, ...]:
    return tuple(generate_tokens(StringIO(source_text).readline))

