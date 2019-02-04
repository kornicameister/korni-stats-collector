import json
import logging
import sys

import click
from jsonmodels import errors as jm_errors

from ksc.collector import github
from ksc.database.firebase import contribution
from ksc.database.firebase import last_run

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

    lr = last_run.LastRun.fetch()
    c = github.collect(lr.date)

    if display:
        click.echo(
            json.dumps({
                'contributions': c.contributions,
                'user': c.user,
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

    try:
        new_contributions = c.contributions

        last_run.LastRun.update(
            lr.key,
            {
                'took_ms': c.took_ms,
                'date': c.until,
                'successful': True,
            },
        )
        contribution.Contribution.save(new_contributions)

    except jm_errors.ValidationError:
        pass


cli.add_command(collect)

if __name__ == '__main__':
    sys.exit(cli())
