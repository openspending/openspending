import collections
import datetime

from economics import Inflation

from openspending.reference import country

InflationResult = collections.namedtuple('Inflation', 'factor value')


class FakeInflation(object):

    def __init__(self, source=None, reference=None, country=None):
        pass

    def get(self, target=None, reference=None, country=None):
        return InflationResult(factor=1.0, value=0.0)

    def inflate(self, amount, target=None, reference=None, country=None):
        return amount


def get_date_object(unparsed_date):
    """
    Parse either a dict or a string to retreive a datetime.date object.
    The dictionary has to be like the one returned by the database, i.e.
    it must have at least three keys, year, month and day.
    The string can be of any of three formats: yyyy, yyyy-mm-dd, or dd-mm-yyyy.
    This method raises a ValueError if it's unable to parse the given object.
    """

    # If unparsed_date is a dict it's probably a time entry as returned by
    # the database so we try to get the data
    if isinstance(unparsed_date, dict):
        try:
            # Year is necessary, month and day can default to 1
            return datetime.date(int(unparsed_date['year']),
                                 int(unparsed_date.get('month', 1)),
                                 int(unparsed_date.get('day', 1)))
        except KeyError:
            # The creation of the datetime.date might return a KeyError but we
            # catch it and just ignore the error. This will mean that we will
            # return a ValueError instead (last line of the method). We do that
            # since the problem is in fact the value of unparsed_date
            pass

    # If unparsed_date is a string (unicode or str) we try to parse it using
    # datetime's builtin date parser
    if isinstance(unparsed_date, basestring):
        # Supported date formats we can parse
        supported_formats = ['%Y', '%Y-%m-%d', '%d-%m-%Y']

        # Loop through the supported formats and try to parse the datestring
        for dateformat in supported_formats:
            try:
                # From parsing we get a datetime object so we call .date() to
                # return a date object
                date = datetime.datetime.strptime(unparsed_date, dateformat)
                return date.date()
            except ValueError:
                # If we get a ValueError we were unable to parse the string
                # with the format so we just pass and go to the next one
                pass

    # If we get here, we don't support the date format unparsed_date is in
    # so we raise a value error to notify of faulty argument.
    raise ValueError('Unable to parse date')


def get_sole_country(territories):
    """
    Get a single country from a list of dataset territories.
    This returns the name of the country as defined in openspending.reference
    """

    # At the moment we only support returning a country if there is only a
    # single territory. If not we raise an error since we don't know which
    # country is the right one
    if len(territories) != 1:
        raise IndexError('Cannot find a sole country')

    return country.COUNTRIES.get(territories[0])


def inflate(amount, target, reference, territories):
    """
    Inflate an amount from a reference year to a target year for a given
    country. Access a global inflation object which is created at startup
    """

    # Get both target and reference dates. We then need to create a new date
    # object since datetime.dates are immutable and we need it to be January 1
    # in order to work.
    target_date = get_date_object(target)
    target_date = datetime.date(target_date.year, 1, 1)
    reference_date = get_date_object(reference)
    reference_date = datetime.date(reference_date.year, 1, 1)

    # Get the country from the list of territories provided
    dataset_country = get_sole_country(territories)

    # Inflate the amount from reference date to the target date
    inflated_amount = app_globals.inflation.inflate(amount, target_date,
                                                    reference_date,
                                                    dataset_country)

    # Return an inflation dictionary where we show the reference and target
    # dates along with original and inflated amounts.
    return {'reference': reference_date, 'target': target_date,
            'original': amount, 'inflated': inflated_amount}

