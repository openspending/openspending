import logging
from flask.ext.script import Manager


from openspending.core import app, db
from openspending.model import Dataset

log = logging.getLogger(__name__)
manager = Manager(app)


@manager.command
def test():
    q = db.session.query(Dataset)
    print q.all()


if __name__ == "__main__":
    manager.run()
