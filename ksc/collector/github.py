import os

import github

from ksc.collector import base

GITHUB_API_KEY: str = 'GITHUB_TOKEN'
GITHUB_USER_KEY: str = 'GITHUB_USER'
GITHUB_PWD_KEY: str = 'GITHUB_PASSWORD'


class GithubStats(dict):
    pass


class GithubCollector(base.Collector):
    def __init__(self) -> None:
        super().__init__()
        self._g: github.Github = None

    def init(self):
        token = os.environ.get(GITHUB_API_KEY, None)
        username = os.environ.get(GITHUB_USER_KEY, None)
        password = os.environ.get(GITHUB_PWD_KEY, None)

        if not (username or password):
            raise base.CollectorConfigurationError(f'Missing env[{GITHUB_USER_KEY}] and env[{GITHUB_PWD_KEY}]')
        elif not token and not (username or password):
            raise base.CollectorConfigurationError(f'Missing env[{GITHUB_API_KEY}]')

        self._g = github.Github(token or username, password)

    def collect(self):
        s = self._g.get_api_status()
        if s.status != 'good':
            raise base.CollectorSourceUnavailable()
        else:
            me = self._g.get_user()
            stats = GithubStats()

            stats['repos'] = {
                'public_count': me.public_repos,
                'private_count': me.total_private_repos
            }
