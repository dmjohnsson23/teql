from dataclasses import dataclass
from enum import Enum


class Opcode(str,Enum):
    delete = 'delete'
    replace = 'replace'
    insert = 'insert'

    def __call__(self, *args):
        return Operation(self, *args)

@dataclass
class Operation:
    opcode:Opcode
    start:int
    end:int
    value:str=None
