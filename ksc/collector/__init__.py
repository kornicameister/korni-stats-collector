import datetime
import typing

from ksc import const
from ksc.collector import github, base


def get_collector(repo: str) \
        -> typing.Callable[[datetime.datetime], base.CollectorResult]:
    if repo == const.GITHUB_REPO:
        return github.collect
