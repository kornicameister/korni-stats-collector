from ksc import const
from ksc.collector import github


def get_collector(repo: str):
    if repo == const.GITHUB_REPO:
        return github.GithubCollector()
