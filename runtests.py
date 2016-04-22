#!/usr/bin/env python

import os
import sys

python = sys.executable

os.chdir('tests')
exit_status = os.system("%s runall.py" % (python))

if exit_status != 0:
    sys.exit(1)
