# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.management.base import BaseCommand, CommandError
import sys
from zoho_api import *


class Command(BaseCommand):
    help = "Run mocks.py under every application"

    def add_arguments(self, parser):
        parser.add_argument('args', metavar='modules', nargs='*')
        parser.add_argument('--auth-token',
                            action='store', dest='auth_token',
                            help="zoho auth token"
                            )

    def handle(self, *modules, **options):
        from django.conf import settings
        verbose = options.get('verbosity', 0)
        if verbose > 2:
            import requests.packages.urllib3
            requests.packages.urllib3.add_stderr_logger()

        token = options.get('auth_token') or getattr(settings, 'ZOHO_AUTH_TOKEN', '')
        if not token:
            raise CommandError("ZOHO_AUTH_TOKEN is not set in SETTING_MODULE ! Please specific with --auth-token")

        client = Client(token)
        format_string = '"{}","{}","{}","{}","{}","{}","{}"\n'
        for module in modules:
            sys.stdout.write("{}\n".format(module))
            sys.stdout.write(
                format_string.format("Section", "Label", "Type", "Custom", "Required", "Readonly", "Max Length"))
            fields = client.get_fields(module)
            for section in fields.sections:
                name = section['name']
                for field in section.fields:
                    sys.stdout.write(format_string.format(
                        name, field['label'], field['type'], field['customfield'],
                        field['req'], field['isreadonly'], field['maxlength']
                    ))

            for field in fields.fields:
                sys.stdout.write(format_string.format(
                    '', field['label'], field['type'], field['customfield'],
                    field['req'], field['isreadonly'], field['maxlength']
                ))

            sys.stdout.write('{}'.format("\n\n"))
