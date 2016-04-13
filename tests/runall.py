#!/usr/bin/env python3

import os
import os.path
import sys

python = sys.executable

exit_status = 0

files = os.listdir('.')
for f in files:
    if not f.endswith('.py') or f == 'runall.py': continue

    status = os.system("%s %s" % (python, f))
    if status != 0:
        exit_status = 1

sys.exit(exit_status)
