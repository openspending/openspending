from collections import defaultdict
from urllib import urlopen

from messytables import CSVRowSet, type_guess
from openspending.lib.util import slugify


def frequent_values(sample):
    values = defaultdict(lambda: defaultdict(int))
    for row in sample:
        for i, value in enumerate(row):
            values[i][value.value] += 1
    sorted_values = []
    for idx, column in values.items():
        frequent = sorted(column.items(), key=lambda (v,c): c, reverse=True)
        sorted_values.append(frequent[:5])
    return sorted_values

def analyze_csv(url, sample=2000):
    try:
        fileobj = urlopen(url)
        row_set = CSVRowSet('data', fileobj, window=sample)
        sample = list(row_set.sample)
        headers, sample = sample[0], sample[1:]
        values = frequent_values(sample)
        types = type_guess(sample)
        mapping = {}
        for header, type_, value in zip(headers, types, values):
            type_ = repr(type_).lower()
            name = slugify(header.value).lower()
            meta = {
                'label': header.value,
                'column': header.value,
                'common_values': value,
                'datatype': type_
                }
            if type_ in ['decimal', 'integer', 'float']:
                meta['type'] = 'measure'
                meta['datatype'] = 'float'
            elif type_ in ['date']:
                meta['type'] = 'date'
                meta['datatype'] = 'date'
            else:
                meta['type'] = 'attribute'
            mapping[name] = meta
        return {'columns': [h.value for h in headers], 
                'mapping': mapping}
    except Exception, e:
        return {'error': unicode(e)}

