import datetime

import pytest

from ksc.collector import base
from ksc.collector.model import collector


class MockedCollector(base.Collector):
    def collect(self) -> collector.Result:
        ...


def test_no_arg_constructor() -> None:
    i = MockedCollector()
    today = datetime.datetime.utcnow()
    assert i.until is None
    assert i.since is not None

    assert i.since.day == today.day
    assert i.since.month == today.month
    assert i.since.year == today.year


def test_since_only_constructor() -> None:
    since = datetime.datetime.utcnow().replace(month=1)
    i = MockedCollector(since=since, until=None)

    assert i.since is not None
    assert i.until is not None


def test_until_only_constructor_fails() -> None:
    until = datetime.datetime.utcnow()
    with pytest.raises(ValueError):
        MockedCollector(since=None, until=until)


def test_if_since_larger_then_until() -> None:
    since = datetime.datetime.utcnow().replace(day=4, month=1)
    until = datetime.datetime.utcnow().replace(day=3, month=1)
    with pytest.raises(ValueError):
        MockedCollector(since=since, until=until)


def test_dates_are_in_utc() -> None:
    since = datetime.datetime.utcnow().replace(day=2, month=1)
    until = datetime.datetime.utcnow().replace(day=3, month=1)
    i = MockedCollector(since=since, until=until)

    assert i.since.tzname() == 'UTC'
    if i.until:
        assert i.until.tzname() == 'UTC'
