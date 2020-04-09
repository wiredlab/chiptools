import sys

# Change these values for your environment
# THIS FILE SHOULD NOT BE READABLE BY OTHERS,
# UPDATE THE FILE PERMISSIONS ACCORDINGLY

# change to the location of this file
sys.path.insert(0, '/var/www/apps/chiptools')

venv_activate = './venv/bin/activate_this.py'
execfile(venv_activate, dict(__file__=venv_activate))

from chiptools import app as application
