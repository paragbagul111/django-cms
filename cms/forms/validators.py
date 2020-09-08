from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, URLValidator
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext

from cms.utils.urlutils import admin_reverse, relative_url_regex


def validate_relative_url(value):
    RegexValidator(regex=relative_url_regex)(value)


def validate_url(value):
    try:
        # Validate relative urls first
        validate_relative_url(value)
    except ValidationError:
        # Fallback to absolute urls
        URLValidator()(value)


def validate_url_uniqueness(site, path, language, user_language=None, exclude_page=None):
    """ Checks for conflicting urls
    """
    from cms.models.pagemodel import PageUrl

    if '/' in path:
        validate_url(path)

    path = path.strip('/')
    page_urls = PageUrl.objects.get_for_site(site, language=language).filter(path=path)

    if exclude_page:
        page_urls = page_urls.exclude(page=exclude_page.pk)

    try:
        conflict_page = page_urls[0].page
    except IndexError:
        return True

    conflict_translation = conflict_page.get_title_obj(language, fallback=False)

    change_url = admin_reverse('cms_pagecontent_change', args=[conflict_translation.pk])

    if user_language:
        change_url += '?language={}'.format(user_language)

    conflict_url = '<a href="%(change_url)s" target="_blank">%(page_title)s</a>' % {
        'change_url': change_url,
        'page_title': force_text(conflict_page),
    }

    if exclude_page:
        message = ugettext('Page %(conflict_page)s has the same url \'%(url)s\' as current page "%(instance)s".')
    else:
        message = ugettext('Page %(conflict_page)s has the same url \'%(url)s\' as current page.')
    message = message % {'conflict_page': conflict_url, 'url': path, 'instance': exclude_page}
    raise ValidationError(mark_safe(message))