import logging
import sys

import click

from ksc import collector
from ksc import const

HELLO_MSG: str = 'ksc - korni-stats-collector'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M',
)


@click.group()
def cli():
    click.echo(HELLO_MSG)


@click.command()
@click.argument('from_repo', type=str, metavar='<from_repo>')
def collect(from_repo: str):
    if from_repo not in const.REPOS:
        raise Exception(f'Unknown repo "{from_repo}"')
    click.echo(f'Spawning collecting the stats from "{from_repo}"')

    c = collector.get_collector(from_repo)
    c.init()
    c.collect()


cli.add_command(collect)

if __name__ == '__main__':
    sys.exit(cli())
