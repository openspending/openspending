from celery.decorators import task

import openspending.command.celery

@task(ignore_result=True)
def greet():
    from openspending.model import Dataset, meta as db
    print "Loaded datasets: "
    for dataset in db.session.query(Dataset):
        print ' * ' + dataset.name





