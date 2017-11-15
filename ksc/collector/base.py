import abc

import six


class CollectorConfigurationError(RuntimeError):
    pass


class CollectorSourceUnavailable(Exception):
    pass


@six.add_metaclass(abc.ABCMeta)
class Collector(object):
    @abc.abstractmethod
    def collect(self):
        pass

    @abc.abstractmethod
    def init(self):
        pass
