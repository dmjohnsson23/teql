from dataclasses import dataclass
from lark import ast_utils, Transformer, v_args
from lark.tree import Meta
import sys
from typing import List, Any, Union

@dataclass
class _Node(ast_utils.Ast):
    pass

@dataclass
class Variable(_Node):
    identifiers:List[Union[str,int]]

@dataclass
class Symbol(_Node):
    name: str

@dataclass
class LiteralPath(_Node):
    path: str

@dataclass
class LiteralRegex(_Node):
    pattern: str
    flags: str = None

@dataclass
class _RangeIndex(_Node):
    pass

@dataclass
class RangeIndexFirst(_RangeIndex):
    n:int = None

@dataclass
class RangeIndexLast(_RangeIndex):
    n:int = None

@dataclass
class RangeIndexNext(_RangeIndex):
    n:int = None

@dataclass
class RangeIndexIndex(_RangeIndex):
    index:int

@dataclass
class RangeIndexRange(_RangeIndex):
    start:int
    end:int
    step:int=1

@dataclass
class _CursorOrSelection(_Node):
    pass

@dataclass
class _Cursor(_CursorOrSelection):
    pass

@dataclass
class _Selection(_CursorOrSelection):
    pass

_StringMatchExpression = Union[Variable,str,LiteralRegex,_Selection]

@dataclass
class StartCursor(_Cursor):
    """place cursor at the start of the current context"""
    pass

@dataclass
class EndCursor(_Cursor):
    """place cursor at the end of the current context"""
    pass

@dataclass
class SelectionAfterCursor(_Cursor):
    """place cursor at the after a selection or cursor"""
    other: _CursorOrSelection
    n: int = None
    def __init__(self, *args):
        if len(args) == 1:
            other = args[0]
        else:
            n = args[0]
            other = args[1]

@dataclass
class SelectionBeforeCursor(_Cursor):
    """place cursor before a selection or cursor"""
    other: _CursorOrSelection
    n: int = None
    def __init__(self, *args):
        if len(args) == 1:
            other = args[0]
        else:
            n = args[0]
            other = args[1]

@dataclass
class SelectionCursor(_Cursor):
    """place a cursor in the context of a selection"""
    inner: _Cursor
    outer: _Selection

@dataclass
class RangeIndexCursor(_Cursor): 
    """if a cursor has multiple matches, select the nth one(s)"""
    ranges: List[_RangeIndex]
    other: _Cursor

@dataclass
class SelectionAfterSelection(_Selection):
    """select everything in context from the end of the other cursor or selection"""
    other: _CursorOrSelection

@dataclass
class SelectionBeforeSelection(_Selection):
    """select everything in context until the start of the other cursor or selection"""
    other: _CursorOrSelection

@dataclass
class DirectLineSelection(_Selection):
    """select a specific line by line number; negative to select from end"""
    ranges: List[_RangeIndex]

@dataclass
class CursorLineSelection(_Selection):
    """select a line by that a cursor sits on"""
    other: _Cursor

@dataclass
class SelectionLineSelection(_Selection):
    """select individual lines of a larger selection"""
    other: _Selection

@dataclass
class FindSelection(_Selection):
    """find a selection"""
    expression: _StringMatchExpression
    is_next:bool = False # TODO belongs to block selector, not here
    is_matching:bool = False # TODO belongs to block selector, not here
    is_line:bool = False
    is_with:bool = False
    def __init__(self, *args):
        self.expression = args[-1]
        for modifier in args[:-1]:
            if modifier is None:
                continue
            modifier = modifier.upper()
            if modifier == 'NEXT':
                self.is_next = True
            elif modifier == 'MATCHING':
                self.is_next = True
            elif modifier in ('LINE', 'LINES'):
                self.is_line = True
            elif modifier == 'WITH':
                self.is_with = True
@dataclass
class BlockSelection(_Selection):
    """select a large block from two other selections"""
    start: _CursorOrSelection
    end: _CursorOrSelection

@dataclass
class BetweenSelection(_Selection):
    """select a large block between two other selections"""
    start: _CursorOrSelection
    end: _CursorOrSelection

@dataclass
class SubSelection(_Selection):
    """select a portion of a previous selection"""
    inner: _Selection
    outer: _Selection

@dataclass
class RangeIndexSelection(_Selection):
    """if a selection has multiple matches, select the nth one"""
    ranges: List[_RangeIndex]
    other: _Selection

@dataclass
class FileSelection(_Selection):
    """select the entire file, escaping from any sub-selection"""
    pass

@dataclass
class _Query(_Node):
    pass

class _UpdateOperation(_Node):
    pass

@dataclass
class UpdateQuery(_Node):
    path:str
    operations:List[_UpdateOperation]
    def __init__(self, path, *operations):
        self.path = path
        self.operations = operations

@dataclass
class InsertOperation(_UpdateOperation):
    string:Union[str,Variable]
    cursor: _Cursor
    is_line:bool = False
    def __init__(self, *args):
        if len(args) == 3 and args[0].upper() in ('LINE', 'LINES'):
            self.is_line = True
            args = args[1:]
        self.string, self.cursor = args

@dataclass
class ChangeOperation(_UpdateOperation):
    selection: Union[_Selection,Variable,str]
    replacement: Union[Variable,str]
    
@dataclass
class DeleteOperation(_UpdateOperation):
    selection: _Selection

@dataclass
class IndentOperation(_UpdateOperation):
    selection: _CursorOrSelection
    amount: int = None
    def __init__(self, *args):
        if len(args) == 2:
            self.amount, self.selection = args
        else:
            self.selection = args[0]

@dataclass
class SelectValue(_Node):
    value:Union[_Selection,Variable,Symbol,str]
    alias:Symbol=None

@dataclass
class SelectQuery(_Node):
    values:List[SelectValue]
    path:str
    def __init__(self, values, path):
        self.values = values
        self.path = path

@dataclass
class SetQuery(_Node):
    key:Union[Variable,Symbol]
    value:Union[str,int,Variable,Symbol]




class ToAst(Transformer):
    # Define extra transformation functions, for rules that don't correspond to an AST class.
    select_values = list
    range_index_list = list

    def NAMED_IDENTIFIER(self, ident):
        return ident

    def POSITIONAL_IDENTIFIER(self, ident):
        return int(ident)

    def LITERAL_STRING(self, s):
        # Remove quotation marks
        return s[1:-1]

    def LITERAL_INT(self, n):
        return int(n)

    def LITERAL_PATH(self, path):
        return path

    def start(self, queries):
        return queries


transformer = ast_utils.create_transformer(sys.modules[__name__], ToAst())