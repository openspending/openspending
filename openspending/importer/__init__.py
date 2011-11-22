import logging

from unidecode import unidecode

from openspending.model import Dataset, meta as db

from openspending.validation import Invalid
from openspending.validation.data import convert_types
from openspending.validation.model import validate_model

log = logging.getLogger(__name__)


class ImporterError(Exception):
    pass


class ModelValidationError(ImporterError):
    def __init__(self, colander_exc):
        self.colander_exc = colander_exc

    def __str__(self):
        msg = []
        msg.append("These errors were found when attempting to validate your " \
                   "model:")
        for k, v in self.colander_exc.asdict().iteritems():
            msg.append("  - '%s' field had error '%s'" % (unidecode(k), unidecode(v)))

        return "\n".join(msg)


class DataError(ImporterError):
    def __init__(self, exception, line_number=None, source_file=None):
        self.exception = exception
        self.line_number = line_number
        self.source_file = source_file

        if isinstance(exception, Invalid):
            msgs = ["Validation error:"]
            for invalid in exception.children:
                msg = "  - '%s' (%s) could not be generated from column '%s'" \
                      " (value: %s): %s"
                msg = msg % (invalid.node.name, invalid.datatype, 
                             invalid.column, invalid.value, invalid.msg)
                msgs.append(msg)
            self.message = "\n".join(msgs)
        elif isinstance(exception, Exception):
            # The message attribute is deprecated for Python 2.6 BaseExceptions.
            self.message = str(exception)
        else:
            self.message = repr(exception)

    def __str__(self):
        return "Line %s: %s" % (self.line_number, self.message)

    def __repr__(self):
        return "<DataError (message='%s', file=%s, line=%d)>" \
            % (self.message, self.source_file, self.line_number)

class TooManyErrorsError(ImporterError):
    pass


class BaseImporter(object):

    def __init__(self, data, model, source_file="<stream>"):
        self.data = data
        self.model = model
        self.model_valid = None
        self.source_file = source_file
        self.errors = []
        self.on_error = lambda e: log.warn(e)

    def run(self,
            dry_run=False,
            max_errors=None,
            max_lines=None,
            raise_errors=False,
            build_indices=True,
            **kwargs):

        self.dry_run = dry_run
        self.max_errors = max_errors
        self.raise_errors = raise_errors

        self.validate_model()
        self.dataset = self.create_dataset(dry_run=dry_run)
        self.dataset.generate()
        #self.describe_dimensions()

        self.line_number = 0

        for line_number, line in enumerate(self.lines, start=1):
            if max_lines and line_number > max_lines:
                break

            self.line_number = line_number
            self.process_line(line)

        if self.line_number == 0:
            self.add_error("Didn't read any lines of data")

        if self.errors:
            log.error("Finished import with %d errors:", len(self.errors))
            for err in self.errors:
                log.error(" - %s", err)
        else:
            log.info("Finished import with no errors!")

    @property
    def lines(self):
        raise NotImplementedError("lines not implemented in BaseImporter")

    def validate_model(self):
        if self.model_valid:
            return

        log.info("Validating model")
        try:
            self.model = validate_model(self.model)
            self.model_valid = True
        except Invalid as e:
            raise ModelValidationError(e)

    def create_dataset(self, dry_run=True):
        q = db.session.query(Dataset)
        q = q.filter_by(name=self.model['dataset']['name'])
        dataset = q.first()
        if dataset is not None:
            return dataset
        dataset = Dataset(self.model)
        # TODO: only persist for non-dry-run?
        if not dry_run:
            db.session.add(dataset)
            db.session.commit()
        return dataset

    def process_line(self, line):
        if self.line_number % 1000 == 0:
            log.info('Imported %s lines' % self.line_number)

        try:
            data = convert_types(self.model['mapping'], line)
            if not self.dry_run:
                self.dataset.load(data)
        except (Invalid, ImporterError) as e:
            if self.raise_errors:
                raise
            else:
                self.add_error(e)

    def add_error(self, exception):
        err = DataError(exception=exception,
                        line_number=self.line_number,
                        source_file=self.source_file)
        self.on_error(err)
        self.errors.append(err)

        if self.max_errors and len(self.errors) >= self.max_errors:
            all_errors = "".join(map(lambda x: "\n  " + str(x), self.errors))
            raise TooManyErrorsError("The following errors occurred:" + all_errors)


from openspending.lib import unicode_dict_reader as udr

class CSVImporter(BaseImporter):

    @property
    def lines(self):
        try:
            return udr.UnicodeDictReader(self.data)
        except udr.EmptyCSVError as e:
            self.add_error(e)
            return ()


