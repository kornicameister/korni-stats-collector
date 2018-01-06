import datetime
import typing

from ksc import const
from ksc.collector import github


def get_collector(repo: str) -> typing.Callable[[datetime.datetime], None]:
    if repo == const.GITHUB_REPO:
        return github.collect
