from datetime import datetime
import typing as t

import pydantic as pd


class APILimitRate(pd.BaseModel):
    limit: int
    remaining: int


class APILimit(pd.BaseModel):
    rate: APILimitRate


class User(pd.BaseModel):
    login: str
    repos_url: str


class Repo(pd.BaseModel):
    name: str
    full_name: str

    commits_url: str
    pulls_url: str
    issues_url: str

    private: bool
    fork: bool


class Issue(pd.BaseModel):
    comments: int


class Branch(pd.BaseModel):
    ref: str
    label: str
    user: User


class PullRequest(pd.BaseModel):
    state: str
    user: User
    assignee: t.Optional[User] = None
    head: Branch
    base: Branch
    author_association: str

    created_at: datetime
    updated_at: datetime
    closed_at: t.Optional[datetime] = None
    merged_at: t.Optional[datetime] = None

    def is_authored_by(self, author: str) -> bool:
        if self.user.login == author:
            return self.author_association.lower() in (
                'owner',
                'contributor',
            )
        else:
            return False


class Commit(pd.BaseModel):
    message: str
