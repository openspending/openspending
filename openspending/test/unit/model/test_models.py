from openspending import model
from openspending.test import DatabaseTestCase, helpers as h

# TODO: the contents of this file needs to be factored out into proper
# decoupled unit tests (test_account.py, etc)

class TestORM(DatabaseTestCase):
    def setup(self):
        super(TestORM, self).setup()
        self.dataset = u'test'
        self.accsrc = u'acc1'
        self.accdst = u'acc2'
        self.amount = 47865
        self.randomkey = u'randomkey'

        dataset = model.Dataset(name=self.dataset)
        dataset.save()

        northeast = model.Classifier(name=u'Northeast', label=u'North east')
        northwest = model.Classifier(name=u'Northwest', label=u'North west')
        pog1 = model.Classifier(name=u'surestart', label=u'Sure start')
        pog2 = model.Classifier(name=u'surestart2', label=u'Another start')
        model.Classifier.c.insert([northeast, northwest, pog1, pog2])

        acc_src = model.Entity(name=self.accsrc, **{
            self.randomkey: u'annakarenina',
            'region': northeast.to_ref_dict()
        })
        acc_dst = model.Entity(name=self.accdst, **{
            self.randomkey: u'orangesarenottheonlyfruit',
            'region': northwest.to_ref_dict()
        })

        model.Entity.c.insert([acc_src, acc_dst])

        entry = model.Entry({
            'amount': self.amount,
            'dataset': dataset.to_ref_dict(),
            'from': acc_src.to_ref_dict(),
            'to': acc_dst.to_ref_dict(),
            'region': northeast.to_ref_dict()
        })

        model.Entry.c.insert(entry)

    def test_01(self):
        dataset = model.Dataset.find_one({'name': self.dataset})

        txn = model.Entry.find_one({
            'dataset': dataset.to_ref_dict(),
            'amount': self.amount
        })

        assert txn

    def test_02(self):
        dataset = model.Dataset.find_one({'name': self.dataset})
        acc_src = model.Entity.find_one({'name': self.accsrc})
        acc_dst = model.Entity.find_one({'name': self.accdst})

        assert acc_src
        assert acc_dst

        northeast = model.Classifier.find_one({'name': u'Northeast'})
        assert northeast.name == u'Northeast', northeast.name

        entry = model.Entry.find_one()
        assert entry['region'] == northeast.to_ref_dict()
        assert entry['from'] == acc_src.to_ref_dict()




