import datetime

from ksc.database.firebase import base


class Meta(base.FirebaseBaseModel):
    ref = u'meta'

    def __init__(self, key: str, last_run: datetime.datetime):
        super().__init__(key)
        self._last_run = last_run

    @property
    def last_run(self) -> datetime.datetime:
        return self._last_run

    @staticmethod
    def from_dict(key, data):
        return Meta(key, data.get('last_run'))

    def to_dict(self):
        return {'last_run': self._last_run}

    @staticmethod
    def update_meta(last_run: datetime.datetime):
        meta = Meta.list(limit=1)[0]
        Meta.update(f'{Meta.ref}/{meta.id}', {'last_run': last_run})
