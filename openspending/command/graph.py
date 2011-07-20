from __future__ import absolute_import

from .base import OpenSpendingCommand
from openspending.model import Dataset, Entry

try:
    import networkx as nx
except ImportError:
    nx = None

class GraphCommand(OpenSpendingCommand):
    summary = "Graph export for OpenSpending datasets."
    usage = "<dataset> <file_name.graphml>"

    parser = OpenSpendingCommand.standard_parser()

    def command(self):
        super(GraphCommand, self).command()

        if not nx:
            print "Could not load 'networkx' module, which is needed for graph"\
                  " command.\nHave you tried `pip install networkx`?"
            return 1

        if len(self.args) != 2:
            GraphCommand.parser.print_help()
            return 1

        dataset_name, file_name = self.args

        g = nx.DiGraph()
        edges = {}
        def _edge(f, t, w):
            ew = edges.get((f, t), 0.0)
            edges[(f, t)] = ew + w

        for entry in Entry.find({"dataset.name": dataset_name}):
            to = entry.get('to')
            if to.get('name') not in g:
                g.add_node(to.get('name'), label=to.get('label'),
                    type='entity', country=to.get('country', ''))
            from_ = entry.get('from')
            if from_.get('name') not in g:
                g.add_node(from_.get('name'), label=from_.get('label'),
                    type='entity', country=from_.get('country', ''))
            _edge(from_.get('name'), to.get('name'), entry.get('amount'))
            for k, v in entry.items():
                if k in ['time', 'dataset', 'from', 'to'] or not isinstance(v, dict):
                    continue
                if v.get('name') not in g:
                    _type = 'classifier'
                    if isinstance(v.get('ref'), dict):
                        _type = v.get('ref').get('$ref')
                    g.add_node(v.get('name'), label=v.get('label', v.get('name')),
                            type=_type)
                #_edge(v.get('name'), to.get('name'), entry.get('amount'))
                #_edge(from_.get('name'), v.get('name'), entry.get('amount'))
        for (f, t), w in edges.items():
            g.add_edge(f, t, weight=w)
        nx.write_graphml(g, file_name)


