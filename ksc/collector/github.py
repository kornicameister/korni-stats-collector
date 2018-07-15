import asyncio
import datetime
import hashlib
import itertools
import logging
import os
import time
import typing
import ujson

import aiohttp
import async_timeout
import purl

from ksc import utils, const
from ksc.collector import base
from ksc.collector.model import github

LOG: logging.Logger = logging.getLogger(__name__)

GITHUB_API_KEY: str = 'GITHUB_TOKEN'
GITHUB_USER_KEY: str = 'GITHUB_USER'
GITHUB_PWD_KEY: str = 'GITHUB_PASSWORD'

REQUEST_TIMEOUT: int = 360

GITHUB_API_URL = 'https://api.github.com'
GITHUB_URLS = {
    'fetch_authenticated_user': f'{GITHUB_API_URL}/user',
    'fetch_all_repos': f'{GITHUB_API_URL}/user/repos',
    'fetch_api_limit': f'{GITHUB_API_URL}/rate_limit'
}
GITHUB_RESPONSE_STATUS_CODES = {'empty_repo': 409}

T = typing.Generic[typing.TypeVar('T', github.APILimit, github.GithubObject)]


async def fetch_user(
    token: str, session: aiohttp.ClientSession
) -> github.User:
    return await fetch_one(
        github.User, token, GITHUB_URLS['fetch_authenticated_user'], session
    )


async def fetch_repos(
    token: str, url: str, session: aiohttp.ClientSession, params: dict = None
) -> typing.List[github.Repo]:
    return await fetch_list(github.Repo, token, url, session, params)


async def fetch_contributions(
    token: str, repo: github.Repo, since: datetime.datetime,
    until: datetime.datetime, author: str, session: aiohttp.ClientSession
):
    def pr_author(r: github.PullRequest):
        return r.author_association.lower() in ['owner', 'contributor'] \
               and r.user.login == author

    def filter_pr_open_since(pr: github.PullRequest):
        return pr.created_at >= since

    def filter_pr_merged_since(pr: github.PullRequest):
        if pr.merged_at is not None:
            return pr.merged_at >= since
        if pr.closed_at is not None:
            return pr.closed_at >= since

    contributions = await asyncio.gather(
        fetch_list(
            github.Commit, token, purl.expand(repo.commits_url), session,
            {'since': since.isoformat()}
        ),
        fetch_list(
            github.Commit, token, purl.expand(repo.commits_url), session, {
                'author': author,
                'since': since.isoformat()
            }
        ),
        fetch_list(
            github.Issue, token, purl.expand(repo.issues_url), session,
            {'since': since.isoformat()}
        ),
        fetch_list(
            github.Issue, token, purl.expand(repo.issues_url), session, {
                'creator': author,
                'since': since.isoformat()
            }
        ),
        fetch_list(
            github.PullRequest, token, purl.expand(repo.pulls_url), session, {
                'base': 'master',
                'state': 'open',
                'sort': 'created'
            }
        ),
        fetch_list(
            github.PullRequest, token, purl.expand(repo.pulls_url), session, {
                'base': 'master',
                'state': 'closed',
                'sort': 'created'
            }
        )
    )

    contributions[4] = list(filter(filter_pr_open_since, contributions[4]))
    contributions[5] = list(filter(filter_pr_merged_since, contributions[5]))

    contributions_lengths = [len(d) for d in contributions]
    LOG.debug(
        f'Contributions count is '
        f'{contributions_lengths} for {repo.name}'
    )

    if utils.ilen(filter(lambda x: x > 0, contributions_lengths)) == 0:
        LOG.info(
            f'{author} has not created neither of (commits,issues,pr) '
            f'in {repo.name} since {since}'
        )
        return None

    commits_count_total = len(contributions[0])
    commits_count_authored = len(contributions[1])
    issues_count_total = len(contributions[2])
    issues_count_authored = len(contributions[3])
    pull_request_count_total_open = len(contributions[4])
    pull_request_count_total_merged = len(contributions[5])
    pull_request_count_authored_open = utils.ilen(
        filter(pr_author, contributions[4])
    )
    pull_request_count_authored_merged = utils.ilen(
        filter(pr_author, contributions[5])
    )

    encoded_repo_name = repo.full_name.encode('utf-8')
    repo_name = (
        repo.full_name
        if not repo.private else hashlib.sha256(encoded_repo_name).hexdigest()
    )

    result = {
        'repo': repo_name,
        'is_fork': repo.fork,
        'is_private': repo.private,
        'platform': const.GITHUB_REPO,
        'from': since,
        'until': until,
        'commits_count': {
            'total': commits_count_total,
            'authored': commits_count_authored
        },
        'issues_count': {
            'total': issues_count_total,
            'authored': issues_count_authored
        },
        'pull_request_count': {
            'total': {
                'open': pull_request_count_total_open,
                'merged': pull_request_count_total_merged
            },
            'authored': {
                'open': pull_request_count_authored_open,
                'merged': pull_request_count_authored_merged
            }
        }
    }

    return result


async def fetch_api_limit(
    token: str, session: aiohttp.ClientSession
) -> github.APILimit:
    return await fetch_one(
        github.APILimit, token, GITHUB_URLS['fetch_api_limit'], session
    )


async def fetch_one(
    model: T,
    token: str,
    url: str,
    session: aiohttp.ClientSession,
    params: dict = None
) -> T:
    LOG.info(f'fetch_one(model={model}, url={url}, params={params})')

    async with async_timeout.timeout(REQUEST_TIMEOUT):
        async with session.get(
            url, params=params, headers={'Authorization': f'token {token}'}
        ) as response:
            raise_for_limit(response)

            return model(**await response.json(loads=ujson.loads))


async def fetch_list(
    model: T,
    token: str,
    url: str,
    session: aiohttp.ClientSession,
    params: dict = None,
    data: typing.List[github.GithubObject] = None
) -> []:
    if data is None:
        data = []

    if params is None:
        params = {}
    params['per_page'] = 1000

    LOG.info(f'fetch_repo_data(model={model}, url={url}, params={params})')

    async with async_timeout.timeout(REQUEST_TIMEOUT):
        async with session.get(
            url, params=params, headers={'Authorization': f'token {token}'}
        ) as response:

            raise_for_limit(response)

            if response.status == GITHUB_RESPONSE_STATUS_CODES['empty_repo']:
                data.extend([])
            else:
                data.extend([
                    model(**d) for d in await response.json(loads=ujson.loads)
                ])

            next_link = utils.get_next_link(response.headers.get('link', ''))
            if next_link:
                return await fetch_list(
                    model, token, next_link, session, params, data
                )
            return data


async def main(since: datetime.datetime,
               until: datetime.datetime,
               token: str) \
        -> base.CollectorResult:
    start = time.time()

    async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
        api_limit = await fetch_api_limit(token, session)

        if api_limit.rate.remaining == 0:
            raise RuntimeError(
                'Cannot start collection, '
                'there is no limit available'
            )
        else:
            LOG.info(f'{api_limit.rate.remaining} requests available')

        user = await fetch_user(token, session)
        repos = await asyncio.gather(
            fetch_repos(token, user.repos_url, session),
            fetch_repos(
                token, GITHUB_URLS['fetch_all_repos'], session,
                {'visibility': 'private'}
            )
        )
        user_contributions = filter(
            None, await asyncio.gather(
                *[
                    fetch_contributions(
                        token, repo, since, until, user.login, session
                    ) for repo in itertools.chain(*repos)
                ]
            )
        )

        return base.CollectorResult(
            user=user.login,
            since=since,
            until=until,
            took_ms=time.time() - start,
            contributions=user_contributions
        )


def raise_for_limit(response):
    remaining = int(response.headers['X-RateLimit-Remaining'])
    if response.status == 403 and remaining == 0:
        raise RuntimeError('API limit exceeded')


def collect(
    last_run_date: datetime.datetime,
    since: typing.Union[None, datetime.datetime],
    until: typing.Union[None, datetime.datetime]
) -> base.CollectorResult:
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        main(
            since or last_run_date, until or datetime.datetime.today(),
            os.environ[GITHUB_API_KEY]
        )
    )
