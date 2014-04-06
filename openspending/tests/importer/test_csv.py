from openspending.model import Dataset, Source
from openspending.model import meta as db
from openspending.lib import json

from openspending.importer import CSVImporter

from openspending.tests.base import DatabaseTestCase
from openspending.tests.helpers import fixture_path, make_account


def csvimport_fixture_path(name, path):
    return fixture_path('csv_import/%s/%s' % (name, path))


def csvimport_fixture_file(name, path):
    try:
        fp = open(csvimport_fixture_path(name, path))
    except IOError:
        if name == 'default':
            fp = None
        else:
            fp = csvimport_fixture_file('default', path)

    return fp


def csvimport_fixture(name):
    model_fp = csvimport_fixture_file(name, 'model.json')
    mapping_fp = csvimport_fixture_file(name, 'mapping.json')
    model = json.load(model_fp)
    if mapping_fp:
        model['mapping'] = json.load(mapping_fp)
    dataset = Dataset(model)
    dataset.generate()
    db.session.add(dataset)
    data_path = csvimport_fixture_path(name, 'data.csv')
    user = make_account()
    source = Source(dataset, user, data_path)
    db.session.add(source)
    db.session.commit()
    return source


class TestCSVImporter(DatabaseTestCase):

    def test_successful_import(self):
        source = csvimport_fixture('successful_import')
        importer = CSVImporter(source)
        importer.run()
        dataset = db.session.query(Dataset).first()

        assert dataset is not None, "Dataset should not be None"
        assert dataset.name == "test-csv"

        entries = dataset.entries()
        assert len(list(entries)) == 4

        # TODO: provenance
        entry = list(dataset.entries(limit=1, offset=1)).pop()
        assert entry is not None, "Entry with name could not be found"
        assert entry['amount'] == 66097.77

    def test_no_dimensions_for_measures(self):
        source = csvimport_fixture('simple')
        importer = CSVImporter(source)
        importer.run()
        dataset = db.session.query(Dataset).first()

        dimensions = [str(d.name) for d in dataset.dimensions]
        assert sorted(dimensions) == ['entry_id', 'from', 'time', 'to']

    def test_successful_import_with_simple_testdata(self):
        source = csvimport_fixture('simple')
        importer = CSVImporter(source)
        importer.run()
        assert importer.errors == 0

        dataset = db.session.query(Dataset).first()
        assert dataset is not None, "Dataset should not be None"

        entries = list(dataset.entries())
        assert len(entries) == 5

        entry = entries[0]
        assert entry['from']['label'] == 'Test From'
        assert entry['to']['label'] == 'Test To'
        assert entry['time']['name'] == '2010-01-01'
        assert entry['amount'] == 100.00

    def test_import_errors(self):
        source = csvimport_fixture('import_errors')

        importer = CSVImporter(source)
        importer.run(dry_run=True)
        assert importer.errors > 1, "Should have errors"

        records = list(importer._run.records)
        assert records[0].row == 1, \
            "Should detect missing date colum in line 1"

    def test_empty_csv(self):
        source = csvimport_fixture('default')
        source.url = 'file:///dev/null'
        importer = CSVImporter(source)
        importer.run(dry_run=True)

        assert importer.errors == 2

        records = list(importer._run.records)
        assert records[0].row == 0
        assert records[1].row == 0
        assert "Didn't read any lines of data" in str(records[1].message)

    def test_malformed_csv(self):
        source = csvimport_fixture('malformed')
        importer = CSVImporter(source)
        importer.run(dry_run=True)
        assert importer.errors == 1

    def test_erroneous_values(self):
        source = csvimport_fixture('erroneous_values')
        importer = CSVImporter(source)
        importer.run(dry_run=True)

        # Expected failures:
        # * unique key constraint not met (2x)
        # * amount cannot be parsed
        # * time cannot be parse
        assert importer.errors == 4

        records = list(importer._run.records)
        # The fourth record should be about badly formed date
        assert "time" in records[3].attribute, \
            "Should find badly formatted date"

        # The row number of the badly formed date should be 5
        assert records[3].row == 5

    def test_error_with_empty_additional_date(self):
        source = csvimport_fixture('empty_additional_date')
        importer = CSVImporter(source)
        importer.run()
        assert importer.errors == 1

    def test_quoting(self):
        source = csvimport_fixture('quoting')
        importer = CSVImporter(source)
        importer.run()
        assert importer.errors == 0


class TestCSVImportDatasets(DatabaseTestCase):

    def count_lines_in_stream(self, f):
        try:
            return len(f.read().splitlines())
        finally:
            f.seek(0)

    def _test_import(self, name):
        source = csvimport_fixture(name)
        data = open(source.url)
        lines = self.count_lines_in_stream(data) - 1  # -1 for header row

        importer = CSVImporter(source)
        importer.run()

        assert importer.errors == 0

        # check correct number of entries
        dataset = db.session.query(Dataset).first()
        entries = list(dataset.entries())
        assert len(entries) == lines

    def test_all_imports(self):
        for dir in ('lbhf', 'mexico', 'sample', 'uganda'):
            yield self._test_import, dir
