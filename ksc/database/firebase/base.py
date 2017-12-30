import abc
import functools

import six

from ksc.database import firebase


@six.add_metaclass(abc.ABCMeta)
class FirebaseBaseModel(object):
    ref: str = None

    def __init__(self, key: str):
        self._key = key

    @abc.abstractmethod
    def to_dict(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def from_dict(key: str, data: dict):
        pass

    @classmethod
    def list(cls, limit: int = None):
        ref = firebase.get_db().collection(cls.ref)

        if limit is not None and limit >= 1:
            ref.limit(limit)

        return [cls.from_dict(i.id, i.to_dict()) for i in ref.get()]

    @classmethod
    @functools.lru_cache(maxsize=10, typed=True)
    def one(cls, key):
        if key is None:
            raise ValueError('Cannot fetch unique element without specified key')

        ref = firebase.get_db().collection(cls.ref).document(key)
        doc = ref.get()

        return cls.from_dict(doc.id, doc.to_dict())
