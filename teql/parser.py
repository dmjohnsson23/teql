import os, sys
from lark import Lark
from .ast import transformer
__all__ = ('parse',)

with open(os.path.join(os.path.dirname(__file__), 'grammar.lark'), 'r') as file:
    parser = Lark(file.read())

def parse(text):
    tree = parser.parse(text)
    return transformer.transform(tree)