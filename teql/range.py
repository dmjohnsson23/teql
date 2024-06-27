from . import ast
from typing import Sequence, Collection

def apply_ranges(ranges:Collection[ast._RangeIndex], select_from:Collection, adapt_index=False):
    prev = -1
    if not isinstance(select_from, Sequence):
        select_from = list(select_from)
    adapter = _1_to_0 if adapt_index else lambda i:i
    for r in ranges:
        if isinstance(r, ast.RangeIndexFirst):
            if r.n is None:
                yield select_from[0]
                prev = 0
            else:
                yield from select_from[:r.n]
                prev = r.n - 1
        if isinstance(r, ast.RangeIndexLast):
            if r.n is None:
                yield select_from[-1]
            else:
                yield from select_from[-r.n:]
            prev = len(select_from) - 1
        if isinstance(r, ast.RangeIndexNext):
            if r.n is None:
                yield select_from[prev+1]
                prev += 1
            else:
                yield from select_from[prev+1:prev+1+r.n]
                prev += r.n
        if isinstance(r, ast.RangeIndexIndex):
            prev = adapter(r.index)
            yield select_from[prev]
        if isinstance(r, ast.RangeIndexRange):
            start = adapter(r.start)
            end = adapter(r.end)
            # Note: index ranges are inclusive (e.g. contain the end value), differing from normal Python ranges
            yield from select_from[start:end+1:r.step]
            # Set prev to the end value of the selected range, or the end value of the full collection; whichever is first
            # TODO account for negative indices
            prev = min(r.end, len(select_from)) 
            if r.step != 1:
                prev -= (prev - r.start) % r.step

def _1_to_0(index):
    if index > 0:
        return index - 1
    if index == 0:
        raise IndexError('TEQL arrays are 1-indexed')
    return index
    

def first(select_from:Collection):
    if not isinstance(select_from, Sequence):
        select_from = list(select_from)
    if select_from:
        return select_from[0]
    

def last(select_from:Collection):
    if not isinstance(select_from, Sequence):
        select_from = list(select_from)
    if select_from:
        return select_from[-1]