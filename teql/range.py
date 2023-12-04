from . import ast
from typing import Sequence, Collection

def apply_ranges(ranges:Collection[ast._RangeIndex], select_from:Collection):
    prev = -1
    if not isinstance(select_from, Sequence):
        select_from = list(select_from)
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
                prev = len(select_from) - 1
            else:
                yield from select_from[-r.n:]
                prev = len(select_from) - r.n
        if isinstance(r, ast.RangeIndexNext):
            if r.n is None:
                yield select_from[prev+1]
                prev += 1
            else:
                yield from select_from[prev+1:prev+1+r.n]
                prev += r.n
        if isinstance(r, ast.RangeIndexIndex):
            yield select_from[r.index]
            prev = r.index
        if isinstance(r, ast.RangeIndexRange):
            yield from select_from[r.start:r.end:r.step]
            prev = min(r.end, len(select_from)) - 1
            if r.step != 1:
                prev -= (prev - r.start) % r.step


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