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
    # def __str__(self):
    #     return self.dump()

@dataclass
class Variable(Node):
    name:str

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

@dataclass
class RangeIndex(Node):
    """
    Represents a range/index statement

    If start is None, this represents the "next" item
    If stop is None, only a single value is returned
    """
    start:int
    stop:int = None
    interval:int = 1

@dataclass
class Selection(Node):
    pass

@dataclass
class Cursor(Node):
    pass

SelectionOrCursor = Union[Selection,Cursor]
StringMatchExpression = Union[Variable,LiteralString,LiteralRegex,Selection]

@dataclass
class IndexCursor(Cursor):
    index:int

@dataclass
class RelativeCursor(Cursor):
    offset:int
    from_end = False
    other:Union[Cursor,Selection]

@dataclass
class SelectionCursor(Cursor):
    offset:int
    other:Selection

@dataclass
class RangeIndexCursor(Cursor):
    index:List[RangeIndex]
    other:Cursor

@dataclass
class DirectLineSelection(Selection):
    line: int

@dataclass
class FindSelection(Selection):
    criteria: StringMatchExpression
    match_line:bool = False
    select_line:bool = False

@dataclass
class BlockSelection(Selection):
    beginning: SelectionOrCursor
    ending: SelectionOrCursor
    inclusive: bool = True

@dataclass
class SubSelection(Selection):
    inner: SelectionOrCursor
    outer: SelectionOrCursor

@dataclass
class RangeIndexSelection(Selection):
    index:List[RangeIndex]
    other:Selection