import re
from ckan.common import _


def url_checker(key, data, errors, context):
    url = data.get(key, None)

    if url:
        # DJango Regular Expression to check URLs
        regex = re.compile(
            r'^https?://'  # scheme is validated separately
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}(?<!-)\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if regex.match(url) is None:
            errors[key].append(_('The URL "%s" is not valid.') % url)
