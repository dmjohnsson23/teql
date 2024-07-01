import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.basename(__file__), '..')))

from .utility_tests import *
from .parser_test import *
from .full_test import *
from .evaluate_selections_test import *
from .evaluate_updates_test import *
from .editor_test import *
from .file_map_test import *
from .context_test import *