from .context import Context
from io import IOBase, TextIOBase, RawIOBase, TextIOWrapper
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
        # TODO can we track the number of lines affected by the change?
        if not isinstance(output, IOBase):
            output = open(output, 'wb')
        if isinstance(output, TextIOBase):
            # Text IO; buffer with a text IO wrapper
            stream = TextIOWrapper(self.stream, encoding=self.context.encoding)
            for line in stream:
                output.write(line)
        else:
            # Binary IO; write directly
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
    
    @property
    def stream(self):
        """
        A file-like object that gives the result of the editor operation
        """
        return EditorStream(self)
        
    def _fast_forward(self, start, end):
        if start > end:
            raise EditorError('Overlapping operations detected')
        yield from self.context.page_bytes(start, end)


class EditorError(Exception):
    pass

class EditorStream(RawIOBase):
    def __init__(self, editor:Editor):
        self._buffer = None
        self.editor = editor
        self._iter = iter(editor)

    def readable(self):
        return True
    
    def seekable(self) -> bool:
        return False
    
    def writable(self) -> bool:
        return False
    
    def readinto(self, byte_buffer):
        max_len = len(byte_buffer)
        try:
            chunk = self._buffer or next(self._iter)
            output, self._buffer = chunk[:max_len], chunk[max_len:]
            actual_len = len(output)
            byte_buffer[:actual_len] = output
            return actual_len
        except StopIteration:
            return 0