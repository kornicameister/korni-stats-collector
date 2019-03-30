import datetime
import typing as t

import pydantic as pd


class CommitsCount(pd.BaseModel):
    total: int
    authored: int


class IssuesCount(pd.BaseModel):
    total: int
    authored: int


class PullRequestCountStat(pd.BaseModel):
    open: int
    merged: int


class PullRequestCount(pd.BaseModel):
    total: PullRequestCountStat
    authored: PullRequestCountStat


class Contribution(pd.BaseModel):
    repo: str
    is_fork: bool
    is_private: bool
    commits_count: CommitsCount
    issues_count: IssuesCount
    pull_request_count: PullRequestCount


class Result(pd.BaseModel):
    user: str
    since: datetime.datetime
    until: datetime.datetime
    took_ms: float
    contributions: t.List[Contribution]
