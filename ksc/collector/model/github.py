from jsonmodels import models, fields


class APILimitRate(models.Base):
    limit = fields.IntField(required=True)
    remaining = fields.IntField(required=True)


class APILimit(models.Base):
    rate = fields.EmbeddedField(APILimitRate, required=True)


class GithubObject(models.Base):
    pass


class User(GithubObject):
    login = fields.StringField(required=True)
    repos_url = fields.StringField(required=True)


class Repo(GithubObject):
    name = fields.StringField(required=True)
    full_name = fields.StringField(required=True)

    commits_url = fields.StringField(required=True)
    pulls_url = fields.StringField(required=True)
    issues_url = fields.StringField(required=True)

    private = fields.BoolField(required=True)
    fork = fields.BoolField(required=True)


class Issue(GithubObject):
    comments = fields.IntField(required=True)


class Branch(GithubObject):
    ref = fields.StringField(required=True)
    label = fields.StringField(required=True)
    user = fields.EmbeddedField(User, required=True, nullable=False)


class PullRequest(GithubObject):
    state = fields.StringField(required=True)
    user = fields.EmbeddedField(User, nullable=True)
    assignee = fields.EmbeddedField(User, nullable=True)
    head = fields.EmbeddedField(Branch, required=True)
    base = fields.EmbeddedField(Branch, required=True)
    author_association = fields.StringField(required=True)


class Commit(GithubObject):
    pass
