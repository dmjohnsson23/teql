from .context import Context
from io import IOBase, TextIOBase
from .operation import Opcode, Operation
from typing import Iterable

class Editor:
    """
    A class that, given a context and list of operations, actually performs the operation
    """
    def __init__(self, context:Context, operations:Iterable[Operation]):
        self.context = context
        self.operations = operations
    
    def __call__(self, output):
        encoding=self.context.encoding
        if not isinstance(output, IOBase):
            output = open(output, 'wb')
        if isinstance(output, TextIOBase):
            if output.encoding != self.context.encoding:
                raise EditorError(f'File encodings do not match; source is {self.context.encoding} and destination is {output.encoding}.')
            output = output.buffer
        with output:
            for block in self:
                output.write(block)
    
    def __iter__(self):
        context_cursor = 0
        for operation in self.operations:
            # Emit unchanged text up to the start of the operation
            yield from self._fast_forward(context_cursor, operation.start)
            # Emit changed text from the operation
            if operation.opcode == Opcode.insert or operation.opcode == Opcode.replace:
                yield operation.value.encode(self.context.encoding)
            # Don't need to yield anything for deletions
            # Move cursor to the end of the operation
            context_cursor = operation.end
        # Emit any unchanged text at the end of the file
        yield from self._fast_forward(context_cursor, self.context.end)
        
    def _fast_forward(self, start, end):
        if start > end:
            raise EditorError('Overlapping operations detected')
        # TODO introduce paging to better work with large files. Could be tricky due to encoding issues.
        yield self.context.bytes(start, end)


class EditorError(Exception):
    pass