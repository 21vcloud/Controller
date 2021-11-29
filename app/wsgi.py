# -*- coding: utf-8 -*-


#python_home = '/data/venv/venv_user_web_console'
#activate_this = python_home + '/bin/activate_this.py'
#execfile(activate_this, dict(__file__=activate_this))

import sys
import os
#sys.path.insert(0, '/var/www/BareMetalControllerBackend')

os.environ["DJANGO_SETTINGS_MODULE"] = "BareMetalControllerBackend.settings"

#from service import app as application

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
sys.path.append("/home/docker/code/app/BareMetalControllerBackend")
