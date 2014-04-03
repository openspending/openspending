from openspending.lib.calculator import TaxCalculator2010

calculator = TaxCalculator2010()


def test_income_tax():
    # Check tax is never more than income.
    def test(income):
        tax, explanation = calculator.total_tax(income)
        tax = tax['tax']
        assert abs(income - tax) >= 0.0, (tax, income, explanation)
        assert (text != '' for text in explanation), (tax, income, explanation)

    # Low incomes.
    yield test, 0
    yield test, 5225

    # High incomes.
    yield test, 2264285.71
    yield test, 10e6

    # Mid-ranking incomes, requiring interpolation.
    yield test, 25837.04
