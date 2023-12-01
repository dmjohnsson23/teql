import os, sys
from lark import Lark, ast_utils
from .ast import *
__all__ = ('parse',)

with open(os.path.join(os.path.dirname(__file__), 'grammar.lark'), 'r') as file:
    parser = Lark(file.read())

transformer = ast_utils.create_transformer(sys.modules[__name__], ToAst())

def parse(text):
    tree = parser.parse(text)
    return transformer.transform(tree)