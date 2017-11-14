import sys

import click

from ksc import const

HELLO_MSG: str = 'ksc - korni-stats-collector'


@click.group()
def cli():
    click.echo(HELLO_MSG)


@click.command()
@click.argument('from_repo', type=str, metavar='<from_repo>')
def collect(from_repo: str):
    if from_repo not in const.REPOS:
        raise Exception(f'Unknown repo "{from_repo}"')
    click.echo(f'Spawning collecting the stats from "{from_repo}"')


cli.add_command(collect)

if __name__ == '__main__':
    sys.exit(cli())
