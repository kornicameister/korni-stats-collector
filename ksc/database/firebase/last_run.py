import datetime

from jsonmodels import fields

from ksc.database.firebase import base


class LastRun(base.FirebaseBaseModel):
    ref = u'meta'

    date = fields.DateTimeField(required=True)
    took_ms = fields.FloatField(required=True)
    successful = fields.BoolField(required=True)

    @staticmethod
    def update_meta(last_run: datetime.datetime) -> None:
        meta = LastRun.list(limit=1)[0]
        LastRun.update(f'{LastRun.ref}/{meta.id}', {'last_run': last_run})

    @staticmethod
    def fetch() -> 'LastRun':
        return LastRun.one('last_run')
