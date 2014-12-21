import logging
from flask.ext.script import Manager


from openspending.core import app

log = logging.getLogger(__name__)
manager = Manager(app)


if __name__ == "__main__":
    manager.run()
