import abc
import datetime
import typing as t

import pytz

from ksc.collector.model import collector


class CollectorConfigurationError(RuntimeError):
    pass


class CollectorSourceUnavailable(Exception):
    pass


class Collector(abc.ABC):
    since: datetime.datetime
    until: t.Optional[datetime.datetime]

    def __init__(
            self,
            since: t.Optional[datetime.datetime] = None,
            until: t.Optional[datetime.datetime] = None,
    ) -> None:
        if since is None and until is None:
            self.since = datetime.datetime.utcnow()
            self.until = None
        elif since is not None and until is None:
            self.since = since
            self.until = datetime.datetime.utcnow()
        elif since is None and until is not None:
            raise ValueError('Cannot collect without knowing where to start')
        elif since is not None and until is not None:
            self.since = since
            self.until = until
        else:
            raise ValueError('Impossible to happen, but it did')

        self.since = pytz.utc.localize(self.since)
        if self.until:
            self.until = pytz.utc.localize(self.until)
            if self.since >= self.until:
                raise ValueError('since cannot be larger or equal to until')

    @abc.abstractmethod
    def collect(self) -> collector.Result:
        pass

    def __repr__(self) -> str:
        return (
            f'Collector {type(self)} '
            f':: since={self.since}, until={self.until}'
        )
