import abc
import functools
import typing
import uuid

import six
from google.cloud.firestore_v1beta1 import DocumentReference

from ksc.database import firebase


@six.add_metaclass(abc.ABCMeta)
class FirebaseBaseModel(object):
    ref: str = None

    def __init__(self, key: str):
        self._key = key

    @property
    def id(self):
        return self._key

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
            raise ValueError(
                'Cannot fetch unique element without specified key'
            )

        ref = firebase.get_db().collection(cls.ref).document(key)
        doc = ref.get()

        return cls.from_dict(doc.id, doc.to_dict())

    @classmethod
    def save(cls, data: typing.List[dict]):
        client = firebase.get_db()
        batch = client.batch()

        for d in data:
            batch.create(
                DocumentReference(cls.ref, str(uuid.uuid4()), client=client), d
            )

        batch.commit()

    @classmethod
    def update(cls, key: str, field_updates: dict):
        client = firebase.get_db()
        client.document(key).update(field_updates)
