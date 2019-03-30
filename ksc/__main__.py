import json
import logging
import sys

import click

from ksc.collector import github

HELLO_MSG: str = 'ksc - korni-stats-collector'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M',
)


@click.group()
def cli() -> None:
    click.echo(HELLO_MSG)


@click.command()
@click.option('--display', type=bool, is_flag=True, metavar='<display>')
@click.option('--no-upload', type=bool, is_flag=True, metavar='<no_upload>')
def collect(display: bool, no_upload: bool) -> None:
    click.echo('Spawning collecting the stats')

    collector_result = github.GithubCollector().collect()

    if display:
        click.echo(
            json.dumps({
                'contributions': collector_result.contributions,
                'user': collector_result.user,
            },
                       indent=2,
                       sort_keys=True),
        )
    if no_upload:
        click.echo(
            '--no-upload flag hes been detected, '
            'skipping uploading to firebase',
        )
        return


cli.add_command(collect)

if __name__ == '__main__':
    sys.exit(cli())
