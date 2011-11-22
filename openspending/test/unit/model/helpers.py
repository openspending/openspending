from tempfile import mkdtemp

SIMPLE_MODEL = {
    'dataset': {
        'name': 'test',
        'label': 'Test Case Model',
        'description': 'I\'m a banana!',
        'unique_keys': ['time', 'to.name', 'function.name']
    },
    'mapping': {
        'amount': {
            'type': 'value',
            'label': 'Amount',
            'column': 'amount',
            'datatype': 'float'
            },
        'time': {
            'type': 'value',
            'label': 'Year',
            'column': 'year',
            'datatype': 'date'
            },
        'field': {
            'type': 'value',
            'label': 'Field 1',
            'column': 'field',
            'datatype': 'string'
            },
        'to': {
            'label': 'Einzelplan',
            'type': 'entity',
            'facet': True,
            'fields': [
                {'column': 'to_name', 'name': 'name', 'datatype': 'string'},
                {'column': 'to_label', 'name': 'label', 'datatype': 'string'},
                {'constant': 'true', 'name': 'const', 'datatype': 'constant'}
            ]
            },
        'function': {
            'label': 'Function code',
            'type': 'classifier',
            'taxonomy': 'funny',
            'facet': False,
            'fields': [
                {'column': 'func_name', 'name': 'name', 'datatype': 'string'},
                {'column': 'func_label', 'name': 'label', 'datatype': 'string'}
            ]
            }
        }
    }

TEST_DATA="""year,amount,field,to_name,to_label,func_name,func_label
2010,200,foo,"bcorp","Big Corp",food,Food & Nutrition
2009,190,bar,"bcorp","Big Corp",food,Food & Nutrition
2010,500,foo,"acorp","Another Corp",food,Food & Nutrition
2009,900,qux,"acorp","Another Corp",food,Food & Nutrition
2010,300,foo,"ccorp","Central Corp",school,Schools & Education
2009,600,qux,"ccorp","Central Corp",school,Schools & Education
"""

def load_dataset(dataset):
    from StringIO import StringIO
    import csv
    from openspending.validation.data import convert_types
    reader = csv.DictReader(StringIO(TEST_DATA))
    for row in reader:
        row = convert_types(SIMPLE_MODEL['mapping'], row)
        dataset.load(row)

#def make_test_app(use_cookies=False):
#    web.app.config['TESTING'] = True
#    web.app.config['SITE_ID'] = '$$$TEST$$$'
#    web.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
#    web.app.config['STAGING_DATA_PATH'] = mkdtemp()
#    core.db.create_all()
#    return web.app.test_client(use_cookies=use_cookies)

def tear_down_test_app():
    pass
#    core.db.session.rollback()
#    core.db.drop_all()


