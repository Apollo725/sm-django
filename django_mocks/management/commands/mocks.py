# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core import management

from django.core.management.base import BaseCommand
import sys
from django.db.models.signals import post_save
from django.dispatch import receiver
import importlib


class Command(BaseCommand):
    help = "Run mocks.py under every application"

    def add_arguments(self, parser):
        parser.add_argument('args', metavar='app_label', nargs='*')
        parser.add_argument('--force', '-f', action='store_true', dest='force',
                            help='force to mock even if the environment is in DEBUG')

    def handle(self, *app_labels, **options):
        from django.conf import settings
        if options.get('force', True) or settings.DEBUG:
            management.call_command('migrate', '--noinput')

            @receiver(post_save)
            def log(sender, instance=None, created=False, **kwargs):
                if created:
                    sys.stderr.write("New instance %s:<%s> is created. \n" % (sender, instance))
                else:
                    sys.stderr.write("Instance %s:<%s> is updated. \n" % (sender, instance))

            if app_labels:
                app_labels = [app_label for app_label in app_labels if app_label in settings.INSTALLED_APPS]
            else:
                app_labels = settings.INSTALLED_APPS

            for app_label in app_labels:
                try:
                    mocks_path = app_label + '.mocks'
                    module = importlib.import_module(mocks_path)
                    if hasattr(module, 'require'):
                        try:
                            module.require()
                        except Exception:
                            sys.stderr.write(mocks_path + ": require condition is not met")
                            continue

                    if hasattr(module, 'mock'):
                        module.mock()
                        sys.stderr.write(mocks_path + " is imported\n")
                except ImportError as e:
                    if 'No module named mocks' not in e.message:
                        raise e

        else:
            sys.stderr.write("Append --force option to make it happen\n")
