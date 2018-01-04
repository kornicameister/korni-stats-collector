import datetime

from ksc import const
from ksc.database.firebase import base


class Contribution(base.FirebaseBaseModel):
    ref = u'contribution'

    def __init__(
        self, key: str, source: str, repo: str, start: datetime.datetime,
        end: datetime.datetime, contributions: dict
    ):
        super().__init__(key)

        if source not in const.REPOS:
            raise Exception(
                f'Unknown source "{source}", must be one of {const.REPOS}'
            )

        self._contributions = contributions
        self._source = source
        self._repo = repo
        self._start = start
        self._end = end

    @staticmethod
    def from_dict(key: str, data: dict):
        return Contribution(
            key=key,
            source=data['source'],
            repo=data['repo'],
            start=data['start'],
            end=data['end'],
            contributions=data['contributions']
        )

    def to_dict(self):
        return {
            'contributions': self._contributions,
            'source': self._source,
            'repo': self._repo,
            'start': self._start,
            'end': self._end,
        }
