import argparse, sys, io
from .teql import TEQL

ap = argparse.ArgumentParser('teql', description="Text Editing Query Language\nThe functionality of grep and sed, with the syntax of SQL")
source_group = ap.add_mutually_exclusive_group()
source_group.add_argument('script', help='The TEQL script to execute')
source_group.add_argument('--interactive', '-i', help='Trigger the interactive shell', action='store_true')

def main():
    args = ap.parse_args()
    if args.interactive:
        interactive_shell()
    elif args.script:
        run_script(args.script)
    else:
        run_script(sys.stdin)


def interactive_shell():
    teql = TEQL()
    buff = []
    is_continued = False
    while True:
        line = input('      ' if is_continued else 'teql> ')
        buff.append(line)
        
        if line.strip().endswith(';') or line.strip == '': # TODO make this smarter
            # consider this the end of the query
            query = '\n'.join(buff)
            buff = []
            try:
                result = teql.execute(query)
                print(result)
            except Exception as e:
                print(e)
                continue
            

def run_script(script):
    teql = TEQL()
    if isinstance(script, io.IOBase):
        script = script.read()
    for result in teql.execute_all(script):
        print(result) # TODO make it prettier