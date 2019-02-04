import abc
import datetime
import typing as t

import six

from ksc.database.firebase import contribution


class CollectorConfigurationError(RuntimeError):
    pass


class CollectorSourceUnavailable(Exception):
    pass


class CollectorResult(object):
    def __init__(
            self,
            user: str,
            since: datetime.datetime,
            until: datetime.datetime,
            took_ms: float,
            contributions: t.Iterable[dict],
    ) -> None:
        self._user = user
        self._since = since
        self._until = until
        self._took_ms = took_ms
        self._contributions = list(contributions)

    @property
    def user(self) -> str:
        return self._user

    @property
    def since(self) -> datetime.datetime:
        return self._since

    @property
    def until(self) -> datetime.datetime:
        return self._until

    @property
    def took_ms(self) -> float:
        return self._took_ms

    @property
    def contributions(self) -> t.List[dict]:
        return self._contributions


@six.add_metaclass(abc.ABCMeta)
class Collector(object):
    @abc.abstractmethod
    def collect(self) -> t.List[contribution.Contribution]:
        pass

    @abc.abstractmethod
    def init(self) -> None:
        pass
