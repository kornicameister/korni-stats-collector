import functools
import re


def parse_link_header(link_header):
    """Extract links and their relations from a Link Header Field."""
    links = [l.strip() for l in link_header.split(',')]
    rels = {}
    pattern = r'<(?P<url>.*)>;\s*rel="(?P<rel>.*)"'
    for link in links:
        group_dict = re.match(pattern, link).groupdict()
        rels[group_dict['rel']] = group_dict['url']
    return rels


def get_next_link(link_header):
    if not link_header:
        return False

    links = parse_link_header(link_header)

    return links.get('next', links.get('last', False))


def ilen(iterable):
    return functools.reduce(lambda x, y: x + 1, iterable, 0)
