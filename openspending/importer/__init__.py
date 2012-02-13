import logging
import traceback
from datetime import datetime

from openspending.model import Run, LogRecord
from openspending.model import meta as db
from openspending.validation.model import Invalid
from openspending.validation.data import convert_types
from openspending.lib import unicode_dict_reader as udr

from openspending.importer import util

log = logging.getLogger(__name__)

class BaseImporter(object):

    def __init__(self, source):
        self.source = source
        self.dataset = source.dataset
        self.errors = 0
        self.row_number = None

    def run(self,
            dry_run=False,
            max_lines=None,
            raise_errors=False,
            **kwargs):

        self.dry_run = dry_run
        self.raise_errors = raise_errors
        
        before_count = len(self.dataset)

        self.row_number = 0

        self._run = Run('import', Run.STATUS_RUNNING,
                        self.dataset, self.source)
        db.session.add(self._run)
        db.session.commit()
        log.info("Run reference: #%s", self._run.id)

        try:
            for row_number, line in enumerate(self.lines, start=1):
                if max_lines and row_number >= max_lines:
                    break

                self.row_number = row_number
                self.process_line(line)
        except Exception as ex:
            self.log_exception(ex)
            if self.raise_errors:
                self._run.status = Run.STATUS_FAILED
                self._run.time_end = datetime.utcnow()
                db.session.commit()
                raise

        if self.row_number == 0:
            self.log_exception(ValueError("Didn't read any lines of data"), 
                    error='')

        num_loaded = len(self.dataset) - before_count
        if not self.errors and num_loaded < (self.row_number-1):
            self.log_exception(ValueError("The number of entries loaded is "
                "smaller than the number of source rows read."),
                error="%s rows were read, but only %s entries created. "
                    "Check the unique key criteria, entries seem to overlap." % \
                    (self.row_number, num_loaded))

        if self.errors:
            self._run.status = Run.STATUS_FAILED
        else:
            self._run.status = Run.STATUS_COMPLETE
            log.info("Finished import with no errors!")
        self._run.time_end = datetime.utcnow()
        db.session.commit()

    @property
    def lines(self):
        raise NotImplementedError("lines not implemented in BaseImporter")

    def process_line(self, line):
        if self.row_number % 1000 == 0:
            log.info('Imported %s lines' % self.row_number)

        try:
            data = convert_types(self.dataset.mapping, line)
            if not self.dry_run:
                self.dataset.load(data)
        except Invalid as invalid:
            for child in invalid.children:
                self.log_invalid_data(child)
            if self.raise_errors:
                raise
        except Exception as ex:
            self.log_exception(ex)
            if self.raise_errors:
                raise

    def log_invalid_data(self, invalid):
        log_record = LogRecord(self._run, LogRecord.CATEGORY_DATA,
                               logging.ERROR, invalid.msg)
        log_record.attribute = invalid.node.name
        log_record.column = invalid.column
        log_record.value = invalid.value
        log_record.data_type = invalid.datatype

        msg = "'%s' (%s) could not be generated from column '%s'" \
              " (value: %s): %s"
        msg = msg % (invalid.node.name, invalid.datatype, 
                     invalid.column, invalid.value, invalid.msg)
        log.warn(msg)
        self._log(log_record)

    def log_exception(self, exception, error=None):
        log_record = LogRecord(self._run, LogRecord.CATEGORY_SYSTEM,
                               logging.ERROR, str(exception))
        if error is not None:
            log_record.error = error
        else:
            log_record.error = traceback.format_exc()
        log.error(unicode(exception))
        self._log(log_record)

    def _log(self, log_record):
        self.errors += 1
        log_record.row = self.row_number
        db.session.add(log_record)
        db.session.commit()


class CSVImporter(BaseImporter):

    @property
    def lines(self):
        try:
            csv = util.urlopen_lines(self.source.url)
            return udr.UnicodeDictReader(csv)
        except udr.EmptyCSVError as e:
            self.log_exception(e)
            return ()


