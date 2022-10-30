# Runtime hook to be used with PyInstaller. This adds the lib/ directory to the path
# used by the PyInstaller boot loader. Some DLLs can be moved there to clean up the
# root directory a bit.

import os
import sys

libdir = os.path.join(os.path.dirname(sys.argv[0]), "lib")
sys.path.append(libdir)
os.environ["PATH"] += os.pathsep + libdir
