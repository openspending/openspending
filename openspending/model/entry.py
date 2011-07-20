from mongo import dictproperty
from changeset import Revisioned
from genshi.template import TextTemplate

from openspending.model import Dataset

class Entry(Revisioned):

    @property
    def context(self):
        return self.get('dataset', {}).get('name')

    id = dictproperty('_id')
    name = dictproperty('name')
    label = dictproperty('label')

    amount = dictproperty('amount')
    currency = dictproperty('currency')

    flags = dictproperty('flags')
    dataset = dictproperty('dataset')

    def render_custom_html(self):
        ds = Dataset.find_one({'name': self.context})

        if ds and ds.entry_custom_html:
            tpl = TextTemplate(ds.entry_custom_html)

            d = dict(self)
            if '_id' in d:
                d['id'] = str(d.pop('_id'))

            ctx = {'entry': d}
            stream = tpl.generate(**ctx)
            return stream.render()
        else:
            return None