import os, sys
from lark import Lark
from lark.exceptions import LarkError
from .ast import transformer
from .exceptions import TEQLException
__all__ = ('parse',)

with open(os.path.join(os.path.dirname(__file__), 'grammar.lark'), 'r') as file:
    parser = Lark(file.read())

def parse(text):
    try:
        tree = parser.parse(text)
    except LarkError as e:
        raise TEQLException(str(e))
    return transformer.transform(tree)