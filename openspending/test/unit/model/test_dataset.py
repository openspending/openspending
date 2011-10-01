from openspending import model

from ... import DatabaseTestCase, helpers as h

def mock_entry():
    return {
        'name': 'testentry',
        'label': 'An Entry'
    }

def mock_dataset():
    return {
        'name': 'testdataset'
    }

class TestDataset(DatabaseTestCase):

    def test_render_entry_custom_html_none(self):
        e = mock_entry()
        d = mock_dataset()
        h.assert_equal(model.dataset.render_entry_custom_html(d, e), None)

    def test_render_entry_custom_html_plain_text(self):
        e = mock_entry()
        d = mock_dataset()
        d['entry_custom_html'] = 'No templating.'
        h.assert_equal(model.dataset.render_entry_custom_html(d, e),
                       'No templating.')

    def test_render_entry_custom_html_genshi_template(self):
        e = mock_entry()
        d = mock_dataset()
        d['entry_custom_html'] = '${entry["name"]}: ${entry["label"]}'
        h.assert_equal(model.dataset.render_entry_custom_html(d, e),
                       'testentry: An Entry')
