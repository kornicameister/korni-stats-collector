import datetime
import logging
import os
import time
from typing import List

import github
from github import NamedUser
from github import PullRequest
from github import Repository

from ksc.collector import base
from ksc.database.firebase import meta

LOG: logging.Logger = logging.getLogger(__name__)

GITHUB_API_KEY: str = 'GITHUB_TOKEN'
GITHUB_USER_KEY: str = 'GITHUB_USER'
GITHUB_PWD_KEY: str = 'GITHUB_PASSWORD'

HARDCODED_REPOS: List[str] = [
    'kornicameister/korni',
    'kornicameister/korni-stats-collector'
]


class GithubStats(object):
    def __init__(self, collected_at: datetime.datetime, since: datetime.datetime, contributions=None):
        self._collected_at = collected_at
        self._since = since
        self._took_ms = None
        self._contributions = contributions

    @property
    def took_ms(self) -> float:
        return self._took_ms

    @took_ms.setter
    def took_ms(self, took_ms: float):
        self._took_ms = took_ms

    def to_dict(self) -> dict:
        return {
            'collected_at': self._collected_at,
            'since': self._since,
            'took_ms': self._took_ms,
            'contributions': self._contributions
        }

    def __repr__(self):
        return f'GS [at={self._collected_at}, since={self._since}, took={self._took_ms}]'


class GithubCollector(base.Collector):
    def __init__(self) -> None:
        super().__init__()
        self._g: github.Github = None
        self._last_stats_meta: meta.Meta = meta.Meta.list(limit=1)[0]

    def init(self):
        token = os.environ.get(GITHUB_API_KEY, None)
        username = os.environ.get(GITHUB_USER_KEY, None)
        password = os.environ.get(GITHUB_PWD_KEY, None)

        if not (username or password) and not token:
            raise base.CollectorConfigurationError(f'Missing env[{GITHUB_USER_KEY}] and env[{GITHUB_PWD_KEY}]')
        elif not token and not (username or password):
            raise base.CollectorConfigurationError(f'Missing env[{GITHUB_API_KEY}]')

        self._g = github.Github(login_or_token=token or username, password=password if token is None else password,
                                per_page=100)

    def collect(self):
        s = self._g.get_api_status()
        if s.status != 'good':
            raise base.CollectorSourceUnavailable()
        else:
            start_ts = time.time()
            me = self._g.get_user()

            stats = GithubStats(
                collected_at=datetime.datetime.today(),
                since=self._last_stats_meta.last_run,
                contributions=self._get_contributions(me)
            )
            stats.took_ms = time.time() - start_ts

            return stats

    def _get_contributions(self, user: NamedUser.NamedUser):
        contributions = dict()

        for repo in [self._g.get_repo(repo, False) for repo in HARDCODED_REPOS]:
            repo: Repository.Repository = repo
            repo_name = repo.name
            repo_collaborators = [c for c in repo.get_collaborators()]

            LOG.info(f'Collecting stats from {repo_name} repository')

            if not filter(lambda c: c.login == user.login, repo_collaborators):
                LOG.warning(f'${user.login} is not a collaborator of {repo_name} repository')
                return contributions

            contributions[f'{repo.owner.login}/{repo_name}'] = {
                'is_fork': repo.fork,
                'is_mine': repo.owner.login == user.login,
                'commit_count': self._count_commits_in_repo(repo, user, self._last_stats_meta.last_run),
                'pull_request_count': self._count_prs_in_repo(repo, user, self._last_stats_meta.last_run)
            }

        return contributions

    @staticmethod
    def _count_prs_in_repo(repo: Repository.Repository, user: NamedUser.NamedUser, since: datetime.datetime):
        open_prs: List[PullRequest] = [pr for pr in repo.get_pulls(state='open', base='master') if
                                       pr.created_at.timestamp() >= since.timestamp()]
        merged_prs: List[PullRequest] = [pr for pr in repo.get_pulls(state='closed', base='master') if
                                         pr.created_at.timestamp() >= since.timestamp()]
        return {
            'total': {
                'open': len(open_prs),
                'merged': len(merged_prs)
            },
            'authored': {
                'open': len([pr for pr in filter(lambda pr: pr.user.login == user.login, open_prs)]),
                'merged': len([pr for pr in filter(lambda pr: pr.user.login == user.login, merged_prs)])
            }
        }

    @staticmethod
    def _count_commits_in_repo(repo: Repository.Repository, user: NamedUser.NamedUser, since: datetime.datetime):
        try:
            return {
                'total': len([c for c in repo.get_commits(since=since)]),
                'authored': len([c for c in repo.get_commits(author=user, since=since)])
            }
        except github.GithubException:
            LOG.exception(f'Failed to count commits in {repo.name}')
            commits = []
        return len(commits)
