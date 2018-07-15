import datetime
import json
import logging
import sys
import typing
import pytz

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

MaybeDatetime = typing.Union[None, datetime.datetime]


class DatetimeArg(click.ParamType):
    name = 'date'

    def __init__(self, fmt: str):
        self._fmt = fmt

    def convert(
        self, value: typing.Union[None, str, datetime.datetime], param, ctx
    ) -> MaybeDatetime:
        if value is None:
            return value

        if isinstance(value, datetime.datetime):
            return value

        try:
            datetime_value = datetime.datetime.strptime(value, self._fmt)
            datetime_value_utc = datetime_value.replace(tzinfo=pytz.UTC)
            return datetime_value_utc
        except ValueError as ex:
            self.fail(
                f'Could not parse datetime string "{value}" formatted as {self._fmt} ({ex})',
                param, ctx
            )


@click.group()
def cli():
    click.echo(HELLO_MSG)


@click.command()
@click.argument('from_repo', type=str, metavar='<from_repo>')
@click.option('--display', type=bool, is_flag=True, metavar='<display>')
@click.option('--no-upload', type=bool, is_flag=True, metavar='<no_upload>')
@click.option('--since', type=DatetimeArg('%Y-%m-%d'))
@click.option('--until', type=DatetimeArg('%Y-%m-%d'))
def collect(
    from_repo: str, display: bool, no_upload: bool, since: MaybeDatetime,
    until: MaybeDatetime
):

    if from_repo not in const.REPOS:
        raise Exception(f'Unknown repo "{from_repo}"')
    click.echo(f'Spawning collecting the stats from "{from_repo}"')

    collector_function = collector.get_collector(from_repo)
    lr = last_run.LastRun.fetch()
    c = collector_function(lr.date, since, until)

    if display:
        click.echo(
            json.dumps({
                'contributions': c.contributions,
                'user': c.user
            },
                       indent=2,
                       sort_keys=True)
        )
    if no_upload:
        click.echo(
            '--no-upload flag hes been detected, '
            'skipping uploading to firebase'
        )
        return

    try:
        new_contributions = c.contributions

        last_run.LastRun.update(
            lr.key, {
                'took_ms': c.took_ms,
                'date': c.until,
                'successful': True
            }
        )
        contribution.Contribution.save(new_contributions)

    except jm_errors.ValidationError:
        pass


cli.add_command(collect)

if __name__ == '__main__':
    sys.exit(cli())
