from jsonmodels import fields, models

from ksc.database.firebase import base


class CommitsCount(models.Base):
    total = fields.IntField(required=True)
    authored = fields.IntField(required=True)


class IssuesCount(models.Base):
    total = fields.IntField(required=True)
    authored = fields.IntField(required=True)


class PullRequestCountStat(models.Base):
    open = fields.IntField(required=True)
    merged = fields.IntField(required=True)


class PullRequestCount(models.Base):
    total = fields.EmbeddedField(PullRequestCountStat, required=True)
    authored = fields.EmbeddedField(PullRequestCountStat, required=True)


class Contribution(base.FirebaseBaseModel):
    ref = u'contribution'
    repo = fields.StringField(required=True)
    is_fork = fields.BoolField(required=True)
    is_private = fields.BoolField(required=True)
    commits_count = fields.EmbeddedField(CommitsCount)
    issues_count = fields.EmbeddedField(IssuesCount)
