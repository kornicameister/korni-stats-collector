import abc
import functools
import logging
import typing
import uuid

import six
from google.cloud.firestore_v1beta1 import DocumentReference
from jsonmodels import models

from ksc.database import firebase

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class FirebaseBaseModel(models.Base):
    ref: str = None

    def __init__(self, **kwargs):
        self._key = kwargs.pop('key')
        super(FirebaseBaseModel, self).__init__(**kwargs)

    @property
    def key(self):
        return self._key

    @classmethod
    def list(cls, limit: int = None):
        LOG.info(f'Listing {cls}')
        ref = firebase.get_db().collection(cls.ref)

        if limit is not None and limit >= 1:
            ref.limit(limit)

        return [cls(key=i.id, **i.to_dict()) for i in ref.get()]

    @classmethod
    @functools.lru_cache(maxsize=10, typed=True)
    def one(cls, key):
        LOG.info(f'Fetching {cls}={key}')
        if key is None:
            raise ValueError(
                'Cannot fetch unique element without specified key'
            )

        ref: DocumentReference = (firebase
                                  .get_db()
                                  .collection(cls.ref)
                                  .document(key))

        doc = ref.get()
        key = ref.id

        return cls(key=key, **doc.to_dict())

    @classmethod
    def save(cls, data: typing.List[typing.Union[models.Base, dict]]):
        LOG.info(f'Saving {len(data)} object of {cls}')
        client = firebase.get_db()
        batch = client.batch()

        for d in data:
            values = d.to_struct() if isinstance(d, FirebaseBaseModel) else d
            ref = DocumentReference(cls.ref, str(uuid.uuid4()), client=client)
            LOG.debug(f'Generated ref {ref} of {cls.ref}')
            batch.create(ref, values)

        batch.commit()

    @classmethod
    def update(cls, key: str, field_updates: dict):
        client = firebase.get_db()
        client.document(cls.ref, key).update(field_updates)
