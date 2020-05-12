#!/usr/bin/env python
from __future__ import absolute_import
import sys
import os.path
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=['mock_now'],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':MEMORY',
            }
        }
     )

    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["mock_now.tests"])
    sys.exit(bool(failures))
