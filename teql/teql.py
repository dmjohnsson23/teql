import sys, os
from glob import glob
from io import TextIOBase
import dataclass
from enum import Enum
from .parser import parse
from . import ast

class TEQL:
    def __init__(self, *, encoding=None):
        self.encoding = encoding or sys.getdefaultencoding()
        self.session_variables = VariableStore()
    
    def execute(self, code:str):
        queries = parse(code)
        if not queries:
            raise Exception('No query to execute')
        if len(queries) > 1:
            raise Exception("Can't execute multiple queries with `execute`, use `execute_all` instead")
        query = queries[0]
        if isinstance(query, ast.UpdateQuery):
            return self._executeUpdateQuery(query)
        elif isinstance(query, ast.SelectQuery):
            return self._executeSelectQuery(query)
        elif isinstance(query, ast.SetQuery):
            return self._executeSetQuery(query)

    def execute_all(self, code:str):
        queries = parse(code)
        if not queries:
            raise Exception('No queries to execute')
        for query in queries:
            if isinstance(query, ast.UpdateQuery):
                yield self._executeUpdateQuery(query)
            elif isinstance(query, ast.SelectQuery):
                yield self._executeSelectQuery(query)
            elif isinstance(query, ast.SetQuery):
                yield self._executeSetQuery(query)
    
    def _executeUpdateQuery(self, query:ast.UpdateQuery):
        for path in glob(query.path):
            opcodes = []
            with open(path, 'r+') as file:
                for operation in query.operations:
                    opcodes.append(self._getUpdateOperationOpcodes(operation, file))
                self._doUpdateOperationOpcodes(opcodes, file)
    
    def _getUpdateOperationOpcodes(self, operation, file):
        """
        Generate a series of opcodes for the operations to apply to the file
        """
        if isinstance(operation, ast.InsertOperation):
            for sel in self._evaluateSelection(operation.cursor):
                # TODO add newlines if operation.is_line = True
                yield Opcode.insert(sel.i1, sel.i2, self._evaluateReplacement(sel, operation.string))
        elif isinstance(operation, ast.ChangeOperation):
            if not isinstance(operation.selection, ast._Selection):
                selection = ast.FindSelection(selection)
            else:
                selection = operation.selection
            for sel in self._evaluateSelection(selection):
                yield Opcode.replace(sel.i1, sel.i2, self._evaluateReplacement(sel, operation.replacement))
        if isinstance(operation, ast.DeleteOperation):
            for sel in self._evaluateSelection(operation.selection):
                yield Opcode.delete(sel.i1, sel.i2)
        if isinstance(operation, ast.IndentOperation):
            # TODO
    
    def _evaluateSelection(self, selector:ast._CursorOrSelection, context):
        """
        Given a cursor or selector statement, yeild a series of real selections with start and end indices.
        """
        if isinstance(selector, ast.StartCursor):
            yield Selection(0,0)
        elif isinstance(selector, ast.EndCursor):
            i = len(context) - 1 # TODO is context a string or a file?
            yield Selection(i,i)
        elif isinstance(selector, ast.SelectionAfterCursor):
            for other in self._evaluateSelection(selector.other, context):
                i = other.i2 + (selector.n or 1) # TODO maybe should be 0
                yield Selection(i,i)
        elif isinstance(selector, ast.SelectionBeforeCursor):
            for other in self._evaluateSelection(selector.other, context):
                i = other.i1 - (selector.n or 1) # TODO maybe should be 0
                yield Selection(i,i)
        elif isinstance(selector, ast.SelectionCursor):
            for other in self._evaluateSelection(selector.outer, context):
                yield from self._evaluateSelection(selector.inner, get_context_of(other)) # TODO get_context_of is a placeholder
        elif isinstance(selector, ast.RangeIndexCursor): 
            # if a cursor has multiple matches, select the nth one(s)
            other = self._evaluateSelection(selector.other, context):
            yield from apply_ranges(selector.ranges, other) # TODO apply_ranges is a placeholder
        if isinstance(selector, ast.SelectionAfterSelection):
            # select everything in context from the end of the other cursor or selection
            other = last(self._evaluateSelection(selector.other, context)) # TODO last is a placeholder
            i = len(context) - 1 # TODO is context a string or a file?
            yield Selection(other.i2, i) # TODO may need to add 1 to other.i2
        if isinstance(selector, ast.SelectionBeforeSelection):
            # select everything in context until the start of the other cursor or selection
            other = last(self._evaluateSelection(selector.other, context)) # TODO last is a placeholder
            yield Selection(0, other.i1) # TODO may need to substract 1 to other.i1
        if isinstance(selector, ast.DirectLineSelection):
            # select a specific line by line number; negative to select from end
            yield from apply_ranges(selector.ranges, select_lines_of(context)) # TODO apply_ranges and select_lines_of are placeholders
        if isinstance(selector, ast.CursorLineSelection):
            # select a line by that a cursor sits on
            # TODO line from selector.other
        if isinstance(selector, ast.SelectionLineSelection):
            # select individual lines of a larger selection
            for other in self._evaluateSelection(selector.outer, context):
                yield from select_lines_of(get_context_of(other)) # TODO select_lines_of and get_context_of are placeholders
        if isinstance(selector, ast.FindSelection):
            # find a selection
            # expression: _StringMatchExpression
            # is_next # relative to previous selection
            # is_matching:bool # same indentation as previous selection
            # is_line:bool # select entire line
            # is_with:bool # match only part of a line even if selecting entire line
            # TODO

        if isinstance(selector, ast.BlockSelection):
            # select a large block from two other selections
            # start: _CursorOrSelection
            # end: _CursorOrSelection
            # TODO
        if isinstance(selector, ast.BetweenSelection):
            # select a large block between two other selections
            # start: _CursorOrSelection
            # end: _CursorOrSelection
            # TODO
        if isinstance(selector, ast.SubSelection):
            # select a portion of a previous selection
            # inner: _Selection
            # outer: _Selection
            # TODO
        if isinstance(selector, ast.RangeIndexSelection):
            # if a selection has multiple matches, select the nth one
            # ranges: List[_RangeIndex]
            # other: _Selection
            # TODO

    def _evaluateReplacement(self, selection, replacement):
        """
        Evaluate a replacement string for the given selection, doing any nessesary string interpolation and formatting
        """
        pass # TODO

    def _doUpdateOperationOpcodes(self, opcodes, file):
        """
        Given a series of opcodes, modify the file
        """
        for opcode in self._normalizeOpcodeList(opcodes):
            pass # todo
    
    def _normalizeOpcodeList(self, opcodes):
        """
        Sort a series of opcodes and ensure that none of them overlap
        """

    def _executeSelectQuery(self, query:ast.SelectQuery):
        pass

    def _executeSetQuery(self, query:ast.SetQuery):
        if isinstance(query.value, ast.Variable):
            value = self.session_variables[query.value.identifiers]
        else:
            value = query.value
        if isinstance(query.key, ast.Symbol):
            if query.key.name == 'encoding':
                if isinstance(value, ast.Symbol):
                    self.encoding = str(value.name)
                elif isinstance(value, str):
                    self.encoding = value
                else:
                    raise ValueError(f"{value} is not valid for encoding")
        elif isinstance(query.key, ast.Variable):
            self.session_variables[query.key.identifiers] = value


class Opcode(str,Enum):
    delete = 'delete'
    replace = 'replace'
    insert = 'insert'

    def __call__(self, *args):
        return Operation(self, *args)

@dataclass
class Selection:
    i1:int
    i2:int
    value:str=None

@dataclass
class Operation:
    opcode:Opcode
    i1:int
    i2:int
    value:str=None

            
class VariableStore:
    def __init__(self):
        self._positional = []
        self._named = {}

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._postitional[index]
        elif isinstance(index, str):
            return self._named[index]
        elif isinstance(index, (list,tuple)):
            if not index:
                return self
            return self.__getitem__(index[0]).__getitem__(index[1:])
        else:
            raise KeyError(index)

    def __setitem__(self, index, value):
        if isinstance(index, int):
            if index >= len(self._positional):
                self._positional.extend([None] * (index - len(self._positional) + 1))
            self._postitional[index] = value
        elif isinstance(index, str):
            self._named[index] = index
        elif isinstance(index, (list,tuple)):
            if not index:
                pass # TODO
            return self.__getitem__(index[0]).__setitem__(index[1:])
        else:
            raise KeyError(index)