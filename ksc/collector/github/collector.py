import asyncio
import datetime
import hashlib
import itertools
import logging
import os
import time
import typing as t

import aiohttp
import async_timeout
import pydantic as pd
import ujson
import yarl

from ksc import utils
from ksc.collector import base
from ksc.collector.github import github
from ksc.collector.model import collector

LOG: logging.Logger = logging.getLogger(__name__)

GITHUB_API_KEY: str = 'GITHUB_TOKEN'
GITHUB_USER_KEY: str = 'GITHUB_USER'
GITHUB_PWD_KEY: str = 'GITHUB_PASSWORD'

REQUEST_TIMEOUT: int = 360

GITHUB_API_URL = yarl.URL('https://api.github.com')
GITHUB_URLS = {
    'fetch_authenticated_user': GITHUB_API_URL / 'user',
    'fetch_all_repos': GITHUB_API_URL / 'user/repos',
    'fetch_api_limit': GITHUB_API_URL / 'rate_limit',
}
GITHUB_RESPONSE_STATUS_CODES = {'empty_repo': 409}

T = t.TypeVar(
    'T',
    github.PullRequest,
    github.Issue,
    github.Commit,
    github.APILimit,
    github.User,
    github.Repo,
)


async def fetch_user(session: aiohttp.ClientSession) -> github.User:
    return await fetch_one(
        github.User,
        GITHUB_URLS['fetch_authenticated_user'],
        session,
    )


async def fetch_repos(
        url: yarl.URL,
        session: aiohttp.ClientSession,
        params: t.Optional[t.Dict[str, str]] = None,
) -> t.List[github.Repo]:
    return await fetch_list(github.Repo, url, session, params)


async def fetch_contributions(
    repo: github.Repo,
    since: datetime.datetime,
    until: datetime.datetime,
    author: str,
    session: aiohttp.ClientSession,
) -> t.Optional[collector.Contribution]:
    def filter_pr_open_since(pr: github.PullRequest) -> bool:
        return pr.created_at >= since

    def filter_pr_merged_since(pr: github.PullRequest) -> bool:
        if pr.merged_at is not None:
            return pr.merged_at >= since
        elif pr.closed_at is not None:
            return pr.closed_at >= since
        return False

    contributions = list(
        await asyncio.gather(
            fetch_list(
                github.Commit,
                yarl.URL(repo.commits_url),
                session,
                {'since': since.isoformat()},
            ),
            fetch_list(
                github.Commit,
                yarl.URL(repo.commits_url),
                session,
                {
                    'author': author,
                    'since': since.isoformat(),
                },
            ),
            fetch_list(
                github.Issue,
                yarl.URL(repo.issues_url),
                session,
                {'since': since.isoformat()},
            ),
            fetch_list(
                github.Issue,
                yarl.URL(repo.issues_url),
                session,
                {
                    'creator': author,
                    'since': since.isoformat(),
                },
            ),
            fetch_list(
                github.PullRequest,
                yarl.URL(repo.pulls_url),
                session,
                {
                    'collector': 'master',
                    'state': 'open',
                    'sort': 'created',
                },
            ),
            fetch_list(
                github.PullRequest,
                yarl.URL(repo.pulls_url),
                session,
                {
                    'collector': 'master',
                    'state': 'closed',
                    'sort': 'created',
                },
            ),
        ),
    )

    contributions[4] = list(filter(filter_pr_open_since, contributions[4]))
    contributions[5] = list(filter(filter_pr_merged_since, contributions[5]))

    contributions_lengths = [len(d) for d in contributions]
    LOG.debug(
        f'Contributions count is '
        f'{contributions_lengths} for {repo.name}',
    )

    if utils.ilen(filter(lambda x: x > 0, contributions_lengths)) == 0:
        LOG.info(
            f'{author} has not created neither of (commits,issues,pr) '
            f'in {repo.name} since {since}',
        )
        return None
    else:
        commits_count_total = len(contributions[0])
        commits_count_authored = len(contributions[1])
        issues_count_total = len(contributions[2])
        issues_count_authored = len(contributions[3])
        pull_request_count_total_open = len(contributions[4])
        pull_request_count_total_merged = len(contributions[5])
        pull_request_count_authored_open = utils.ilen(
            filter(lambda pr: pr.is_authored_by(author), contributions[4]),
        )
        pull_request_count_authored_merged = utils.ilen(
            filter(lambda pr: pr.is_authored_by(author), contributions[5]),
        )

        repo_name = (
            repo.full_name if not repo.private else
            hashlib.sha256(repo.full_name.encode('utf-8')).hexdigest()
        )

        return collector.Contribution(
            repo=repo_name,
            is_fork=repo.fork,
            is_private=repo.private,
            commits_count=collector.CommitsCount(
                total=commits_count_total,
                authored=commits_count_authored,
            ),
            issues_count=collector.IssuesCount(
                total=issues_count_total,
                authored=issues_count_authored,
            ),
            pull_request_count=collector.PullRequestCount(
                total=collector.PullRequestCountStat(
                    open=pull_request_count_total_open,
                    merged=pull_request_count_total_merged,
                ),
                authored=collector.PullRequestCountStat(
                    open=pull_request_count_authored_open,
                    marged=pull_request_count_authored_merged,
                ),
            ),
        )


async def fetch_api_limit(session: aiohttp.ClientSession) -> github.APILimit:
    return await fetch_one(
        github.APILimit,
        GITHUB_URLS['fetch_api_limit'],
        session,
    )


async def fetch_one(
        model: t.Type[T],
        url: yarl.URL,
        session: aiohttp.ClientSession,
        params: t.Optional[t.Dict[str, str]] = None,
) -> T:
    LOG.info(f'fetch_one(model={model}, url={url}, params={params})')

    async with async_timeout.timeout(REQUEST_TIMEOUT):
        async with session.get(url, params=params) as response:
            raise_for_limit(response)
            return model.parse_obj(await response.json())


async def fetch_list(
        model: t.Type[T],
        url: yarl.URL,
        session: aiohttp.ClientSession,
        params: t.Optional[t.Dict[str, str]] = None,
        data: t.Optional[t.List[T]] = None,
) -> t.List[T]:
    if data is None:
        data = []

    if params is None:
        params = {}
    params['per_page'] = str(1000)

    LOG.info(f'fetch_repo_data(model={model}, url={url}, params={params})')

    async with async_timeout.timeout(REQUEST_TIMEOUT):
        async with session.get(url, params=params) as response:
            raise_for_limit(response)

            def parse_obj_safe(d: t.Any) -> t.Optional[T]:
                try:
                    return model.parse_obj(d)
                except pd.ValidationError:
                    LOG.exception(
                        f'Failed to parse [{d}, {type(d)}] as {model}',
                    )
                    return None

            if response.status == GITHUB_RESPONSE_STATUS_CODES['empty_repo']:
                data.extend([])
            else:
                response_obj = await response.json()
                if isinstance(response_obj, list):
                    response_data = filter(
                        lambda x: x is not None,
                        (parse_obj_safe(d) for d in response_obj),
                    )
                    for rd in response_data:
                        if rd is not None:
                            data.append(rd)
                else:
                    LOG.warning(
                        'Received non iterable response, '
                        'when list was expected',
                        extra=dict(response=response_obj),
                    )

            next_link = utils.get_next_link(response.headers.get('link', ''))
            if next_link:
                return await fetch_list(
                    model,
                    next_link,
                    session,
                    params,
                    data,
                )
            return data


async def main(
        last_run_date: datetime.datetime,
        token: str,
) -> collector.Result:
    start = time.time()

    async with aiohttp.ClientSession(
            json_serialize=ujson.dumps,
            headers={'Authorization': f'token {token}'},
    ) as session:
        api_limit = await fetch_api_limit(session)

        if api_limit.rate.remaining == 0:
            raise RuntimeError(
                'Cannot start collection, there is no limit available',
            )
        else:
            LOG.info(f'{api_limit.rate.remaining} requests available')

        user = await fetch_user(session)
        repos = await asyncio.gather(
            fetch_repos(yarl.URL(user.repos_url), session),
            fetch_repos(
                GITHUB_URLS['fetch_all_repos'],
                session,
                {'visibility': 'private'},
            ),
        )

        user_contributions: t.List[collector.Contribution] = list(
            filter(
                None,
                await asyncio.gather(
                    *[
                        fetch_contributions(
                            repo,
                            last_run_date,
                            datetime.datetime.today(),
                            user.login,
                            session,
                        ) for repo in itertools.chain(*repos)
                    ],
                ),
            ),
        )

        return collector.Result(
            user=user.login,
            since=last_run_date,
            until=datetime.datetime.today(),
            took_ms=time.time() - start,
            contributions=user_contributions,
        )


def raise_for_limit(response: aiohttp.ClientResponse) -> None:
    remaining = int(response.headers.get('X-RateLimit-Remaining', -1))
    if response.status == 403 and remaining == 0:
        raise RuntimeError('API limit exceeded')


class GithubCollector(base.Collector):
    def collect(self) -> collector.Result:
        return asyncio.run(main(
            self.since,
            os.environ[GITHUB_API_KEY],
        ))
