from .context import Context
from io import IOBase, TextIOBase, RawIOBase, TextIOWrapper, BytesIO
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
    
    def _blocks_by_lines(self, merge_distance=1):
        file_map = self.context.file_map
        first_line = last_line = diff_first_line = diff_last_line = None
        block_ops = []
        line_delta = 0
        for op in self.operations:
            op_start_line = file_map.cursor_to_line(op.start)
            if first_line is not None and op_start_line - last_line > merge_distance:
                # There is a previous block, but this op is not adjacent and need not be combined
                yield first_line, last_line, diff_first_line, diff_last_line, block_ops
                block_ops = []
                first_line = op_start_line
                diff_first_line = op_start_line + line_delta
            elif first_line is None:
                # We are starting a new block
                first_line = op_start_line
                diff_first_line = op_start_line + line_delta
            block_ops.append(op)
            # Adjust the line delta based on the operation's change
            if op.opcode == Opcode.insert:
                line_delta += op.value.count("\n")
            elif op.opcode == Opcode.delete:
                line_delta -= self.context.string(op.start, op.end).count("\n")
            elif op.opcode == Opcode.replace:
                line_delta += op.value.count("\n")
                line_delta -= self.context.string(op.start, op.end).count("\n")
            # Expand the block to include the last line
            last_line = file_map.cursor_to_line(op.end)
            diff_last_line = last_line + line_delta
        if block_ops:
            yield first_line, last_line, diff_first_line, diff_last_line, block_ops

    
    def patch(self):
        """
        Outputs the operations in the unified diff format used by Git and by the `patch` command-line utility.

        Yields lines of the patch file
        """
        # TODO context lines
        # TODO check for unchanged lines
        # Could just use difflib to generate a diff rather than doing it ourselves?
        yield "--- before\n"
        yield "+++ after\n"
        for first_line, last_line, diff_first_line, diff_last_line, block_ops in self._blocks_by_lines():
            yield f"@@ -{first_line},{last_line-first_line+1} +{diff_first_line},{diff_last_line-diff_first_line+1} @@\n"
            sub_context = self.context.sub(block_ops[0].start, block_ops[-1].end).expand_to_lines()
            old_lines = sub_context.split_lines_string()
            for line in old_lines:
                yield f"- {line}"
            sub_editor = Editor(sub_context, [Operation(
                op.opcode, 
                op.start - sub_context.start, 
                op.end - sub_context.end, 
                op.value
            ) for op in block_ops])
            new_lines = BytesIO()
            sub_editor(new_lines)
            new_lines.seek(0)
            for line in TextIOWrapper(new_lines, encoding=self.context.encoding):
                yield f"+ {line}"





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