import logging
import os
import time
from typing import List

import github
from github import NamedUser
from github import PullRequest
from github import Repository

from ksc.collector import base

LOG: logging.Logger = logging.getLogger(__name__)

GITHUB_API_KEY: str = 'GITHUB_TOKEN'
GITHUB_USER_KEY: str = 'GITHUB_USER'
GITHUB_PWD_KEY: str = 'GITHUB_PASSWORD'

HARDCODED_REPOS: List[str] = [
    'kornicameister/korni',
    'kornicameister/korni-stats-collector'
]


class GithubStats(object):
    def __init__(self, timestamp=None, contributions=None):
        self._timestamp = timestamp
        self._took_ms = None
        self._contributions = contributions

    @property
    def timestamp(self):
        return self._timestamp if self._timestamp else time.time()

    @property
    def contributions(self):
        return self._contributions if self._contributions else {}

    @property
    def took_ms(self):
        return self._took_ms

    @took_ms.setter
    def took_ms(self, took_ms: float):
        self._took_ms = took_ms


class GithubCollector(base.Collector):
    def __init__(self) -> None:
        super().__init__()
        self._g: github.Github = None

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

            stats = GithubStats(contributions=self._get_contributions(me))
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
                'commit_count': self._count_commits_in_repo(repo, user),
                'pull_request_count': self._count_prs_in_repo(repo, user)
            }

        return contributions

    @staticmethod
    def _count_prs_in_repo(repo: Repository.Repository, user: NamedUser.NamedUser):
        open_prs: List[PullRequest] = [pr for pr in repo.get_pulls(state='open', base='master')]
        merged_prs: List[PullRequest] = [pr for pr in repo.get_pulls(state='closed', base='master')]
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
    def _count_commits_in_repo(repo: Repository.Repository, user: NamedUser.NamedUser):
        try:
            return {
                'total': len([c for c in repo.get_commits()]),
                'authored': len([c for c in repo.get_commits(author=user)])
            }
        except github.GithubException:
            LOG.exception(f'Failed to count commits in {repo.name}')
            commits = []
        return len(commits)
