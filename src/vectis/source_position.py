from dataclasses import dataclass
from typing import NamedTuple
from typing import str, int

@dataclass
class SourcePosition:
    line: int
    column: int
    file: str

    def __post_init__(self):
        if self.line < 1:
            raise ValueError("Invalid source position: line must be >= 1")
        if self.column < 1:
            raise ValueError("Invalid source position: column must be >= 1")
        if not self.file:
            raise ValueError("Invalid source position: file must not be empty")
