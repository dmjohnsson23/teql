import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.basename(__file__), '..')))
from teql.cli import main
main()