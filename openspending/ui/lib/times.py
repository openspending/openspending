'''
Create datastructures for times and dates that should be used
to save dates and times in the database, especially for
:attr:`openspending.model.Entries.times`

Like most parts of our data models date and date ranges are persisted
denormalized. We save both single dates and date ranges in a a special
kind of date range datastructure that conains

* the daterange as a single string
* the start and the end date as

  * a datetime object
  * a string
  * year, month and day as seperate stings

This works like this::

  >>> from openspending.ui.lib.times import for_year
  >>> for_year(2011)
  {'from': {'day': '20110301',
            'month': '201103',
            'parsed': datetime.datetime(2011, 3, 1, 0, 0),
            'year': '2011'},
   'to': {'day': '20110331',
          'month': '201103',
          'parsed': datetime.datetime(2011, 3, 31, 0, 0),
          'year': '2011'},
   'unparsed': '2011-03'}
'''
import calendar
from datetime import datetime

from openspending.ui.forms.entry import PLACEHOLDER

GRANULARITY = {
        "daily": "time.from.month",
        "day": "time.from.month",
        "week": "time.from.month",
        "weekly": "time.from.month",
        "monthly": "time.from.month",
        "month": "time.from.month",
        "year": "time.from.year",
        "yearly": "time.from.year",
        "annual": "time.from.year"
    }

EMPTY_DATE = {
    'unparsed': PLACEHOLDER,
    'from': {'parsed': None,
             'year': PLACEHOLDER,
             'month': PLACEHOLDER,
             'day': PLACEHOLDER},
    'to': {'parsed': None,
           'year': PLACEHOLDER,
           'month': PLACEHOLDER,
           'day': PLACEHOLDER}}


def timespan(unparsed, from_date, to_date):
    '''Create a datastructure to save a span between tow datetimes
    in the database.

    ``unparsed``
        The timespan as a string
    ``from_date``
        The start date as a ``datetime``
    ``to_date``
        The end date as a ``datetime``

    returns: a `dict` representing the timespan that can be saved into
    the database
    '''
    assert isinstance(from_date, datetime), ("from_date is not properly "
                                             "formatted!")
    assert isinstance(to_date, datetime), "to_date is not properly formatted!"
    return {
            'unparsed': unparsed,
            'from': {
                'parsed': from_date,
                'year': str(from_date.year),
                'month': from_date.strftime("%Y%m"),
                'day': from_date.strftime("%Y%m%d")
                },
            'to': {
                'parsed': to_date,
                'year': str(to_date.year),
                'month': to_date.strftime("%Y%m"),
                'day': to_date.strftime("%Y%m%d")
                }
            }


def for_year(year):
    '''Create a :func:`timespan` datastructure for a year

    ``year``
         A year as a `str` or `int`

    returns: see :func:`timespan`
    '''
    year_i = int(year)
    return timespan(year, datetime(year_i, 1, 1), datetime(year_i, 12, 31))


def for_datestrings(date1, date2=None):
    '''Create a :func:`timespan` for a date or between a start
    and a end date, given as strings.

    ``date1``
        start date as a string in a format that can be read by
        :func:`from_datestring`
    ``date2``
        end date as a string in a format that can be read by
        :func:`from_datestring`, or ``None`` if start and end date
        are identical.

    returns: see :func:`timespan`
    '''
    date_start, date_end = from_datestrings(date1, date2)
    if date2 is None:
        return timespan(date1, date_start, date_end)
    else:
        return timespan("%s|%s" % (date1, date2), date_start, date_end)


def fill_date(date, fill_tuple, offset=1):
    '''Not API.
    fill a date list so that it can be used to initialize ``datetime`` objects

    ``date``
        An tuple representing a ``datetime`` that may lack elements required
        to be used to initialize datetime objects.
    ``fill_tuple``
        A tuple containing information how to fill the ``date``
    '''
    for i in range(offset, len(fill_tuple) + 1):
        if len(date) - i == 0:
            date.append(fill_tuple[i - offset](*date[:i]))
    return date


def from_datestrings(date1, date2=None):
    '''convert a start date ``date1`` and a end date ``date2`` into
    ``datetime`` objects.
    The strings can have the format ``yyyy-mm-dd``, ``yyyy-mm`` or ``yyyy``.
    The dates are completed to full start or end dates by determinating
    the start or end of the year or month.

    If ``date2`` is none, the end date is computed from the string ``date1``
    '''
    # these tuples contain information how to fill the month or day
    # position of a datetime for starting or ending dates
    fill_start = (lambda y: 1, lambda y, m: 1)
    fill_end = (lambda y: 12, lambda y, m: calendar.monthrange(y, m)[1])

    date_start = [int(x) for x in date1.split("-")]
    date_start = fill_date(date_start, fill_start)
    date_start = datetime(*date_start)

    if date2 is None:
        date_end = [int(x) for x in date1.split("-")]
    else:
        date_end = [int(x) for x in date2.split("-")]
    date_end = fill_date(date_end, fill_end)
    date_end = datetime(*date_end)

    return date_start, date_end

if __name__ == '__main__':
    print from_datestrings("2011-01", "2011-02")
    print from_datestrings("2011", "2012-02-03")
