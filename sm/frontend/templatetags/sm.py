# coding=utf-8
from __future__ import absolute_import

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter(name='country_code')
@stringfilter
def country_code(value):
    if value == 'en':
        return 'us'
    if value == 'ko':
        return 'kr'
    if value == 'ja':
        return 'jp'
    return value.split('-')[-1]


@register.filter(name='lang_code')
@stringfilter
def lang_code(value):
    return value.split('-')[0]


@register.filter(name="currency_symbol")
@stringfilter
def currency_symbol(value):
    if value == 'EUR':
        return '€'
    return '$'
