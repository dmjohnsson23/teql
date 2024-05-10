import sys, os
from glob import glob
from io import TextIOBase
from dataclasses import dataclass
from enum import Enum

from .exceptions import TEQLException
from .parser import parse
from . import ast
from .context import Context
from .range import apply_ranges, first, last
from typing import List, Iterable, Optional

class TEQL:
    def __init__(self, *, encoding=None, line_separator=None):
        self.encoding = encoding or sys.getdefaultencoding()
        self.line_separator = line_separator or os.linesep
        self.line_numbers = None
        self.use = None
        self.session_variables = VariableStore()
    
    def execute(self, code:str):
        queries = parse(code)
        if not queries:
            raise TEQLException('No query to execute')
        if len(queries) > 1:
            raise TEQLException("Can't execute multiple queries with `execute`, use `execute_all` instead")
        query = queries[0]
        if isinstance(query, ast.UpdateQuery):
            return self._executeUpdateQuery(query)
        elif isinstance(query, ast.ShowQuery):
            return self._executeShowQuery(query)
        elif isinstance(query, ast.SelectQuery):
            return self._executeSelectQuery(query)
        elif isinstance(query, ast.SetQuery):
            return self._executeSetQuery(query)
        elif isinstance(query, ast.UseQuery):
            return self._executeUseQuery(query)

    def execute_all(self, code:str):
        queries = parse(code)
        if not queries:
            raise TEQLException('No queries to execute')
        for query in queries:
            if isinstance(query, ast.UpdateQuery):
                yield self._executeUpdateQuery(query)
            elif isinstance(query, ast.ShowQuery):
                yield self._executeShowQuery(query)
            elif isinstance(query, ast.SelectQuery):
                yield self._executeSelectQuery(query)
            elif isinstance(query, ast.SetQuery):
                yield self._executeSetQuery(query)
            elif isinstance(query, ast.UseQuery):
                yield self._executeUseQuery(query)

    def _iterFileContexts(self):
        path_found = False
        for path in glob(self.use):
            path_found = True
            with open(path, 'r+b') as file:
                yield Context(file, encoding=self.encoding, line_separator=self.line_separator)
        if not path_found:
            raise TEQLException(f"File(s) not found: {self.use}")
        
    def _executeShowQuery(self, query:ast.ShowQuery):
        if isinstance(query.value.value, ast._Selection):
            for context in self._iterFileContexts():
                for selection in self._evaluateSelection(query.value.value, context):
                    print(selection.string())
        # TODO all the other things we could show
    
    def _executeSelectQuery(self, query:ast.SelectQuery):
        return SelectResult(self._executeSelectQueryGetStores(query))
    
    def _executeSelectQueryGetStores(self, query:ast.SelectQuery):
        path_found = False
        for path in glob(query.path):
            path_found = True
            store = VariableStore()
            store[0] = path
            index = 1
            with open(path, 'r+b') as file:
                context = Context(file, encoding=self.encoding, line_separator=self.line_separator)
                for value in query.values:
                    evaluated = self._evaluateSelectValue(value, context)
                    store[index] = evaluated
                    if value.alias is not None:
                        store[value.alias.name] = evaluated
                    index += 1
            yield store
        if not path_found:
            raise TEQLException(f"File(s) not found: {query.path}")
    
    def _evaluateSelectValue(self, value:ast.SelectValue, context: Context):
        if isinstance(value.value, ast._Selection):
            return VariableStore([
                selection.string() for selection in self._evaluateSelection(value.value, context)
            ])
        # TODO other types

    
    def _executeUpdateQuery(self, query:ast.UpdateQuery):
        for path in glob(query.path):
            opcodes = []
            with open(path, 'r+b') as file:
                context = Context(file, encoding=self.encoding, line_separator=self.line_separator)
                for operation in query.operations:
                    opcodes.append(self._getUpdateOperationOpcodes(operation, context))
                self._doUpdateOperationOpcodes(opcodes, context)
    
    def _getUpdateOperationOpcodes(self, operation, context:Context):
        """
        Generate a series of opcodes for the operations to apply to the file
        """
        if isinstance(operation, ast.InsertOperation):
            for sel in self._evaluateSelection(operation.cursor, context):
                # TODO add newlines if operation.is_line = True
                yield Opcode.insert(sel.start, sel.end, self._evaluateReplacement(sel, operation.string))
        elif isinstance(operation, ast.ChangeOperation):
            if not isinstance(operation.selection, ast._Selection):
                selection = ast.FindSelection(selection)
            else:
                selection = operation.selection
            for sel in self._evaluateSelection(selection, context):
                yield Opcode.replace(sel.start, sel.end, self._evaluateReplacement(sel, operation.replacement))
        if isinstance(operation, ast.DeleteOperation):
            for sel in self._evaluateSelection(operation.selection, context):
                yield Opcode.delete(sel.start, sel.end)
        if isinstance(operation, ast.IndentOperation):
            # TODO
            pass
    
    def _evaluateSelection(self, selector:ast._CursorOrSelection, context:Context):
        """
        Given a cursor or selector statement, yield a series of real selections with start and end indices.
        """
        if isinstance(selector, ast.StartCursor):
            yield context.sub(0,0)
        elif isinstance(selector, ast.EndCursor):
            i = len(context)
            yield context.sub(i,i)
        elif isinstance(selector, ast.SeekCursor):
            i = selector.offset
            if (i < 0):
                i = len(context) + i
            yield context.sub(i, i)
        elif isinstance(selector, ast.OffsetCursor):
            for other in self._evaluateSelection(selector.other, context):
                i = other.start + selector.offset
                yield context.sub(i, i)
        elif isinstance(selector, ast.SelectionAfterCursor):
            for other in self._evaluateSelection(selector.other, context):
                i = other.end + (selector.n or 1) # TODO maybe should be 0
                yield context.sub(i,i)
        elif isinstance(selector, ast.SelectionBeforeCursor):
            for other in self._evaluateSelection(selector.other, context):
                i = other.start - (selector.n or 1) # TODO maybe should be 0
                yield context.sub(i,i)
        elif isinstance(selector, ast.SelectionCursor):
            for other in self._evaluateSelection(selector.outer, context):
                yield from self._evaluateSelection(selector.inner, context.sub(other.s1, other.s2))
        elif isinstance(selector, ast.RangeIndexCursor): 
            # if a cursor has multiple matches, select the nth one(s)
            other = self._evaluateSelection(selector.other, context)
            yield from apply_ranges(selector.ranges, other, adapt_index=True)
        elif isinstance(selector, ast.SelectionAfterSelection):
            # select everything in context from the end of the other cursor or selection
            other = last(self._evaluateSelection(selector.other, context))
            i = len(context)
            yield context.sub(other.end, i)
        elif isinstance(selector, ast.SelectionBeforeSelection):
            # select everything in context until the start of the other cursor or selection
            other = first(self._evaluateSelection(selector.other, context))
            yield context.sub(0, other.start) # TODO may need to subtract 1 to other.start
        elif isinstance(selector, ast.SubstringSelection):
            # select everything in context until the start of the other cursor or selection
            yield context.sub(selector.start, selector.end)
        elif isinstance(selector, ast.DirectLineSelection):
            # select a specific line by line number; negative to select from end
            yield from apply_ranges(selector.ranges, context.expand_to_lines().split_lines(), adapt_index=True)
        elif isinstance(selector, ast.CursorLineSelection):
            # select a line by that a cursor sits on
            yield context.expand_to_lines()
        elif isinstance(selector, ast.SelectionLineSelection):
            # select individual lines of a larger selection
            for other in self._evaluateSelection(selector.other, context):
                yield from other.expand_to_lines().split_lines()
        elif isinstance(selector, ast.FindSelection):
            # find a selection
            # TODO include modifiers:
            # is_next # relative to previous selection
            # is_matching:bool # same indentation as previous selection
            # is_line:bool # select entire line
            # is_with:bool # match only part of a line even if selecting entire line
            if isinstance(selector.expression, str):
                yield from context.find_all(selector.expression)
            elif isinstance(selector.expression, ast.LiteralRegex):
                yield from context.find_all_re(selector.expression.pattern, selector.expression.flags)
            elif isinstance(selector.expression, ast.Variable):
                pass # TODO
            elif isinstance(selector.expression, ast._Selection):
                pass # TODO
        elif isinstance(selector, ast.BlockSelection):
            # select a large block from two other selections
            start = first(self._evaluateSelection(selector.start, context))
            end = last(self._evaluateSelection(selector.end, context))
            # Ensure both ends exist and the end is after the start
            if start is not None and end is not None and start.end <= end.start:
                yield context.sub(start.start, end.end)
        elif isinstance(selector, ast.BetweenSelection):
            # select a large block between two other selections
            start = first(self._evaluateSelection(selector.start, context))
            end = last(self._evaluateSelection(selector.end, context))
            # Ensure both ends exist and the end is after the start
            if start is not None and end is not None and start.end <= end.start:
                yield context.sub(start.end, end.start)
        elif isinstance(selector, ast.SubSelection):
            # select a portion of a previous selection
            for other in self._evaluateSelection(selector.outer, context):
                yield from self._evaluateSelection(selector.inner, other)
        elif isinstance(selector, ast.RangeIndexSelection):
            # if a selection has multiple matches, select the nth one
            yield from apply_ranges(selector.ranges, self._evaluateSelection(selector.other, context), adapt_index=True)
        elif isinstance(selector, ast.FileSelection):
            yield context.file()

    def _evaluateReplacement(self, selection, replacement):
        """
        Evaluate a replacement string for the given selection, doing any necessary string interpolation and formatting
        """
        pass # TODO

    def _doUpdateOperationOpcodes(self, opcodes, file):
        """
        Given a series of opcodes, modify the file
        """
        for opcode in self._normalizeOpcodeList(opcodes):
            pass # todo
    
    def _normalizeOpcodeList(self, opcodes:List['Operation']):
        """
        Sort a series of opcodes by reverse index, and ensure that none of them overlap
        """
        prev = None
        for opcode in sorted(opcodes, key=lambda op: op.start, reverse=True):
            if prev is not None and opcode.end > prev.start:
                raise TEQLException(f'Conflicting/overlapping operations: {opcode} and {prev}')
            prev = opcode
            yield opcode

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
            if query.key.name == 'linesep':
                if isinstance(value, str):
                    self.encoding = value
                elif isinstance(value, ast.Symbol) and value.name.lower() in ('posix','unix','lf'):
                    self.line_separator = "\n"
                elif isinstance(value, ast.Symbol) and value.name.lower() in ('windows','dos','crlf'):
                    self.line_separator = "\r\n"
                elif isinstance(value, ast.Symbol) and value.name.lower() == 'cr':
                    self.line_separator = "\r"
                elif isinstance(value, ast.Symbol) and value.name.lower() == 'lfcr':
                    self.line_separator = "\n\r"
                else:
                    raise ValueError(f"{value} is not valid for encoding")
            if query.key.name == 'linenumbers':
                if isinstance(value, str):
                    self.line_numbers = value
                elif isinstance(value, ast.Symbol) and value.name.lower() == 'on':
                    self.line_numbers = "{} "
                elif isinstance(value, ast.Symbol) and value.name.lower() == 'off':
                    self.line_numbers = None
                else:
                    raise ValueError(f"{value} is not valid for linenumbers")
        elif isinstance(query.key, ast.Variable):
            self.session_variables[query.key.identifiers] = value
    
    def _executeUseQuery(self, query:ast.UseQuery):
        self.use = query.path

class Opcode(str,Enum):
    delete = 'delete'
    replace = 'replace'
    insert = 'insert'

    def __call__(self, *args):
        return Operation(self, *args)

@dataclass
class Selection:
    start:int
    end:int

@dataclass
class Operation:
    opcode:Opcode
    start:int
    end:int
    value:str=None

            
class VariableStore:
    def __init__(self, *args):
        self._positional = []
        self._named = {}
        for arg in args:
            if isinstance(arg, list):
                self._positional.extend(arg)
            if isinstance(arg, dict):
                self._named.update(arg)

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._positional[index]
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
            self._positional[index] = value
        elif isinstance(index, str):
            self._named[index] = index
        elif isinstance(index, (list,tuple)):
            if not index:
                pass # TODO
            return self.__getitem__(index[0]).__setitem__(index[1:])
        else:
            raise KeyError(index)
    
    def __repr__(self):
        return f"VariableStore({repr(self._positional)}, {repr(self._named)})"


class Result:
    pass

class SelectResult(Result):
    def __init__(self, stores:Iterable[VariableStore]):
        self._stores = iter(stores)
    
    def fetch(self)->Optional[VariableStore]:
        try:
            return next(self._stores)
        except StopIteration:
            return None
    
    def fetch_all(self)->List[VariableStore]:
        return list(self._stores)
    
    def fetch_iter(self)->Iterable[VariableStore]:
        yield from self._stores
        
class UpdateResult(Result):
    pass
class SetResult(Result):
    pass

class UseResult(Result):
    pass