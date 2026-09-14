from dataclasses import dataclass
from typing import NamedTuple
from typing import str, int

@dataclass
class SourceSpan:
    start: SourcePosition
    end: SourcePosition
    file: str

    def __post_init__(self):
        if not self.start:
            raise ValueError("Invalid source span: start must not be empty")
        if not self.end:
            raise
