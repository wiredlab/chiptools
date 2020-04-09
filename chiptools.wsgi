import os
import sys

# Change these values for your environment
# THIS FILE SHOULD NOT BE READABLE BY OTHERS,
# UPDATE THE FILE PERMISSIONS ACCORDINGLY

# change to the location of this file
this_dir = '/var/www/apps/chiptools'
sys.path.insert(0, this_dir)

activate_this = os.path.join(this_dir, 'venv/bin/activate_this.py')
with open(activate_this) as f:
    exec(f.read(), dict(__file__=activate_this))

from chiptools import app as application
