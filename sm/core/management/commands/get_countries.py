# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.management.base import BaseCommand, CommandError
from sm.core.models import Country
import requests


class Command(BaseCommand):
    help = "Retrieve list of countries from https://restcountries.eu/rest/v2/all and add them to the db"

    def handle(self, *args, **options):
        Country.objects.all().delete()
        json = requests.get('https://restcountries.eu/rest/v2/all').json()

        for country in json:
            if country['region'] == 'Europe':
                Country.objects.create(name=country['name'], code=country['alpha2Code'], currency='EUR',
                                       continent=country['region'], trans=country['nativeName'])
            else:
                if not country['currencies'][0]['code'] or (
                        country['currencies'][0]['code'] != 'USD' and
                        country['currencies'][0]['code'] != 'CAD' and
                        country['currencies'][0]['code'] != 'EUR'):
                    Country.objects.create(name=country['name'], code=country['alpha2Code'], currency='USD',
                                           continent=country['region'], trans=country['nativeName'])
                else:
                    Country.objects.create(name=country['name'], code=country['alpha2Code'],
                                           currency=country['currencies'][0]['code'],
                                           continent=country['region'], trans=country['nativeName'])
