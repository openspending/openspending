from openspending.lib import unicode_dict_reader as udr

from openspending.etl.importer.base import BaseImporter

class CSVImporter(BaseImporter):

    @property
    def lines(self):
        try:
            return udr.UnicodeDictReader(self.data)
        except udr.EmptyCSVError as e:
            self.add_error(e)
            return ()

