import argparse, sys, io
from .teql import TEQL

ap = argparse.ArgumentParser('teql', description="Text Editing Query Language\nThe functionality of grep and sed, with the syntax of SQL")
ap.add_argument('script', help='The TEQL script to execute', nargs='?')

def main():
    args = ap.parse_args()
    if args.script is None:
        from .interactive_shell import InteractiveShell
        InteractiveShell().run()
    elif args.script == '-':
        run_script(sys.stdin)
    else:
        run_script(args.script)
            

def run_script(script):
    teql = TEQL()
    if isinstance(script, io.IOBase):
        script = script.read()
    for result in teql.execute_all(script):
        print(result) # TODO make it prettier