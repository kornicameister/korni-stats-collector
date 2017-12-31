import abc
import typing

import six

from ksc.database.firebase import contribution


class CollectorConfigurationError(RuntimeError):
    pass


class CollectorSourceUnavailable(Exception):
    pass


@six.add_metaclass(abc.ABCMeta)
class Collector(object):
    @abc.abstractmethod
    def collect(self) -> typing.List[contribution.Contribution]:
        pass

    @abc.abstractmethod
    def init(self):
        pass
