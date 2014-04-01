import csv
from StringIO import StringIO

# National statistics for tax paid per household income decile, 2008/9.
# Taken from Table 14 in http://www.statistics.gov.uk/CCI/article.asp?ID=2440
# Row 1 is average gross income per decile - including benefits, pensions etc
# Row 2 is average direct taxation - income tax, employee NI and council tax
# Row 3 is average total indirect taxation MINUS VAT, tobacco, alcohol, & car costs
# Row 4 is average total VAT paid
# Row 5 is average total tobacco tax paid
# Row 6 is average total alcohol tax (beer, cider, wine & spirits) paid
# Row 7 is average total car-related costs (petrol & car tax)
# We connect the data points by linear interpolation.
reader = csv.reader(StringIO('''
0,9219,13583,17204,22040,25190,32995,37592,46268,56889,94341
0,1172,1368,1939,3108,3973,6118,7423,10172,13463,23047
0,1016,969,1125,1262,1319,1507,1630,1884,2148,2622
0,1101,1085,1295,1562,1609,1927,2155,2616,2871,3747
0,288,310,317,320,295,341,286,311,235,251
0,150,167,182,243,222,261,306,392,450,526
0,349,289,373,505,519,632,727,851,909,949
'''))
income_table = list(reader)
income_table = [[(float(income)) for income in row] for row in income_table]


class TaxCalculator2010(object):

    def total_tax(self,
                  income,
                  spending=None,
                  is_smoker=True,
                  is_drinker=True,
                  is_driver=True,
                  ):
        '''Estimates a person's tax contribution based on the following
        information.

        :param income: Total household income. This is used to estimate both
          direct and indirect tax paid.
        :param spending: Household expenditure. No longer used, but included
          for back-compatibility.
        :param is_smoker: - `True` if the person smokes, or `False` if not.
          Default is True.
        :param is_drinker: - `True` if the person drinks, or `False` if not.
          Default is True.
        :param is_driver: - `True` if the person drives a car, `False` if not.
          Default is True.

        :returns: a pair `(total_tax, explanation)`. The `explanation` is a list of
            strings describing the steps of the calculation.
        '''
        lower = 0.0
        income = float(income)
        explanation = []
        tax_results = {}
        if income <= 0.0:
            tax_results['tax'] = 0.0
            explanation.append('Incomes must be positive.')
            return tax_results, explanation

        # First, find the relevant income deciles.
        for i, upper in enumerate(income_table[1]):
            if income < upper:
                # Found the right band. Use linear interpolation.
                explanation.append('''\
This household income falls between national average income decile %s (which has average \
gross household income of %.2f, and pays %.2f in direct tax, %.2f in VAT, \
%.2f in smoking taxes, %.2f in alcohol-related taxes, %.2f in car-related taxes, \
and %.2f in other indirect taxes), and decile %s (which has average gross \
household income of %.2f, and pays %.2f in direct tax, %.2f in VAT, \
%.2f in smoking taxes, %.2f in alcohol-related taxes, %.2f in car-related taxes, \
and %.2f in other indirect taxes).'''
                                   % (i - 1, lower,
                                      income_table[2][
                                          i - 1], income_table[3][i - 1],
                                      income_table[4][
                                          i - 1], income_table[5][i - 1],
                                      income_table[6][
                                          i - 1], income_table[7][i - 1],
                                      i, upper,
                                      income_table[2][i], income_table[3][i],
                                      income_table[4][i], income_table[5][i],
                                      income_table[6][i], income_table[7][i]))
                # Linear interpolation.
                multiplier = (income - lower) / (upper - lower)
                tax_results['total_direct_tax'] = income_table[2][i - 1] + \
                    (income_table[2][i] - income_table[2][i - 1]) * multiplier
                indirect_tax_minus_extras = income_table[3][i - 1] + \
                    (income_table[3][i] - income_table[3][i - 1]) * multiplier
                tax_results['vat'] = income_table[4][i - 1] + \
                    (income_table[4][i] - income_table[4][i - 1]) * multiplier
                if is_smoker:
                    tax_results['tobacco_tax'] = income_table[5][i - 1] + \
                        (income_table[5][i] - income_table[5]
                         [i - 1]) * multiplier
                else:
                    tax_results['tobacco_tax'] = 0
                if is_drinker:
                    tax_results['alcohol_tax'] = income_table[6][i - 1] + \
                        (income_table[6][i] - income_table[6]
                         [i - 1]) * multiplier
                else:
                    tax_results['alcohol_tax'] = 0
                if is_driver:
                    tax_results['car_related_tax'] = income_table[7][i - 1] + \
                        (income_table[7][i] - income_table[7]
                         [i - 1]) * multiplier
                else:
                    tax_results['car_related_tax'] = 0
                break
            else:
                lower = upper
        else:
            # Income is above all the bands. Use constant tax rates.
            direct_top_rate = income_table[2][-1] / income_table[1][-1]
            indirect_top_rate = income_table[3][-1] / income_table[1][-1]
            vat_top_rate = income_table[4][-1] / income_table[1][-1]
            tax_results['total_direct_tax'] = income * direct_top_rate
            indirect_tax_minus_extras = income * indirect_top_rate
            tax_results['vat'] = income * vat_top_rate
            if is_smoker:
                tax_results['tobacco_tax'] = income * \
                    (income_table[5][-1] / income_table[1][-1])
            else:
                tax_results['tobacco_tax'] = 0
            if is_drinker:
                tax_results['alcohol_tax'] = income * \
                    (income_table[6][-1] / income_table[1][-1])
            else:
                tax_results['alcohol_tax'] = 0
            if is_drinker:
                tax_results['car_related_tax'] = income * \
                    (income_table[7][-1] / income_table[1][-1])
            else:
                tax_results['car_related_tax'] = 0
            explanation.append('''\
For very high-earning households, in the top income decile, we don't use linear interpolation,
but assume the fractions of income paid as tax are the average for the top decile.''')

        # Calculate indirect tax by adding up all the other kinds of tax.
        tax_results['total_indirect_tax'] = indirect_tax_minus_extras + \
            tax_results['vat'] + tax_results['tobacco_tax'] + \
            tax_results['alcohol_tax'] + tax_results['car_related_tax']

        # Set up the explanation text.
        explanation_text = 'Therefore, a'
        if not is_smoker:
            explanation_text += ' non-smoking'
        if not is_drinker:
            explanation_text += ' non-driving'
        if not is_driver:
            explanation_text += ' non-driving'
        explanation_text += ' household with an income of %.2f pays approximately %.2f' \
                            'in direct tax and %.2f in total indirect tax.' % \
                            (income,
                             tax_results['total_direct_tax'],
                                tax_results['total_indirect_tax'])
        explanation.append(explanation_text)

        tax_results['tax'] = tax_results['total_direct_tax'] + \
            tax_results['total_indirect_tax']

        return tax_results, explanation
