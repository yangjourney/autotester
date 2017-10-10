"""
WSGI config for autotester project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os
import site
import sys
SITE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(SITE_DIR)
#site_packages = os.path.join(PROJECT_ROOT, 'env/lib/python2.6/site-packages')
site_packages = os.path.join(PROJECT_ROOT, 'C:\Python36\Lib\site-packages')
site.addsitedir(os.path.abspath(site_packages))
#sys.path.insert(0, "/var/www/autotester")
#sys.path.insert(1, "/var/www/autotester/autotester")
sys.path.insert(0, "D:\tools\APItesttools\buglife-autotester-beta1.0\autotester")
sys.path.insert(1, "D:\tools\APItesttools\buglife-autotester-beta1.0\autotester\autotester\autotester")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autotester.settings")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)
