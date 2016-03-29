#!/usr/bin/env python3

import os
import os.path
import sys

python = 'python3'

files = os.listdir('.')
for f in files:
    if not f.endswith('.py') or f == 'runall.py': continue

    os.system("%s %s" % (python, f))
