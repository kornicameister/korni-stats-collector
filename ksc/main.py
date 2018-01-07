import logging
import sys

import click
from jsonmodels import errors as jm_errors

from ksc import collector
from ksc import const
from ksc.database.firebase import contribution
from ksc.database.firebase import last_run

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

    collector_function = collector.get_collector(from_repo)
    lr = last_run.LastRun.fetch()
    c = collector_function(lr.date)

    try:
        new_contributions = c.contributions

        last_run.LastRun.update(lr.key, {
            'took_ms': c.took_ms,
            'date': c.until,
            'successful': True
        })
        contribution.Contribution.save(new_contributions)

    except jm_errors.ValidationError:
        pass


cli.add_command(collect)

if __name__ == '__main__':
    sys.exit(cli())
