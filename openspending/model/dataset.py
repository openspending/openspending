from mongo import Base, dictproperty
from changeset import Revisioned

class Dataset(Revisioned):

    id = dictproperty('_id')
    name = dictproperty('name')
    label = dictproperty('label')
    description = dictproperty('description')
    currency = dictproperty('currency')
    entry_custom_html = dictproperty('entry_custom_html')

    def get_regions(self):
        if not "regions" in self:
            self["regions"] = []
        return self["regions"]

    def add_region(self, region):
        regions = set(self.get_regions())
        regions.add(region)
        self["regions"] = list(regions)

    @classmethod
    def find_by_region(cls, region):
        return Dataset.find({"regions": region})

    @classmethod
    def distinct_regions(cls):
        return Dataset.c.distinct("regions")
