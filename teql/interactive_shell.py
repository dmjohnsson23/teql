import atexit
import os
import readline
from .teql import TEQL, UpdateResult, SelectResult, SetResult

class InteractiveShell:
    def __init__(self):
        self.teql = TEQL()
    
    def load_history(self, histfile=None):
        if histfile is None:
            histfile = os.path.join(os.path.expanduser("~"), ".teql_history")
        try:
            readline.read_history_file(histfile)
            h_len = readline.get_current_history_length()
        except FileNotFoundError:
            open(histfile, 'wb').close()
            h_len = 0
        atexit.register(self.save_history, h_len, histfile)

    def save_history(self, prev_h_len, histfile):
        new_h_len = readline.get_current_history_length()
        readline.set_history_length(1000)
        readline.append_history_file(new_h_len - prev_h_len, histfile)

    def run(self):
        self.load_history()
        readline.parse_and_bind('"\M-[A": previous-history')
        readline.parse_and_bind('"\M-[B": next-history')
        buff = []
        is_continued = False
        while True:
            try:
                line = input('      ' if is_continued else 'teql> ')
            except KeyboardInterrupt:
                print()
                break
            except EOFError:
                print()
                break
            buff.append(line)
            is_continued = True
            if line.strip().endswith(';') or line.strip() == '': # TODO make this smarter
                # consider this the end of the query
                query = '\n'.join(buff)
                buff = []
                is_continued = False
                if query.strip():
                    try:
                        result = self.teql.execute(query)
                        if isinstance(result, SelectResult):
                            for store in result.fetch_all():
                                print(store)
                        elif isinstance(result, UpdateResult):
                            print(result) # TODO
                        elif isinstance(result, SetResult):
                            print(result) # TODO
                        else:
                            print(result)
                    except Exception as e:
                        print(e)
                        continue