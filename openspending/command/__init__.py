# command.py
#
# The leaf classes in this module implement Paste Script commands; they
# are runnable with "paster thing", where thing is one of the commands
# listed in the openspending section of "paster help".
#
# They are registered in openspending's setup.py.
#
# See http://pythonpaste.org/script/developer.html for documentation of
# Paste Script.
from __future__ import absolute_import

from .db import DbCommand
from .solr import SolrCommand
from .remove_entries import RemoveEntriesCommand
from .user import GrantAdminCommand
from .graph import GraphCommand
