from dataclasses import dataclass, field
from typing import List, Any, Union

@dataclass
class Node:
    _str: str = field(init=False, repr=False)
    _pos: int = field(init=False, repr=False)
    def _parsedata(self, s, pos):
        self._str = s
        self._pos = pos
        return self
    def __str__(self):
        return self.dump()
    
@dataclass
class Selection(Node):
    start: int
    end: int

@dataclass
class Literal(Node):
    value: Any
    def dump(self, indent_level=0):
        return repr(self.value) # TODO make better

@dataclass
class LiteralString(Literal):
    value: str

@dataclass
class LiteralRegex(Literal):
    value: str
    def dump(self, indent_level=0):
        v = self.value.replace('/', '\\/')
        return f"/{v}/"

@dataclass
class LiteralInt(Literal):
    value: int

@dataclass
class LiteralFloat(Literal):
    value: float