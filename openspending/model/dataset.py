from .base import Base, dictproperty
from genshi.template import TextTemplate

class Dataset(Base):

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

    def render_entry_custom_html(self, entry):
        return self._render_custom_html(self.entry_custom_html, entry)

    def _render_custom_html(self, tpl, obj):
        if tpl:
            tpl = TextTemplate(tpl)

            ctx = {'entry': obj}
            stream = tpl.generate(**ctx)
            return stream.render()
        else:
            return None