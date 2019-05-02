import functools
import re
import typing as t

import yarl


def parse_link_header(link_header: str) -> t.Dict[str, str]:
    """Extract links and their relations from a Link Header Field."""
    links = [l.strip() for l in link_header.split(',')]
    rels = {}
    pattern = r'<(?P<url>.*)>;\s*rel="(?P<rel>.*)"'
    for link in links:
        match = re.match(pattern, link)
        if not match:
            continue
        else:
            group_dict = match.groupdict()
            rels[group_dict['rel']] = group_dict['url']
    return rels


def get_next_link(link_header: t.Optional[str]) -> t.Optional[yarl.URL]:
    if not link_header:
        return None

    links = parse_link_header(link_header)
    maybe_link = links.get('next', links.get('last', None))

    return yarl.URL(maybe_link) if maybe_link is not None else None


def ilen(iterable: t.Iterable[t.Any]) -> int:
    return functools.reduce(lambda x, y: x + 1, iterable, 0)
