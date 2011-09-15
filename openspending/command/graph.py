from openspending import model

try:
    import networkx as nx
except ImportError:
    nx = None

def graph(dataset_name, file_name):
    if not nx:
        print "Could not load 'networkx' module, which is needed for graph"\
              " command.\nHave you tried `pip install networkx`?"
        return 1

    g = nx.DiGraph()
    edges = {}

    def _edge(f, t, w):
        ew = edges.get((f, t), 0.0)
        edges[(f, t)] = ew + w

    for entry in model.entry.find({"dataset.name": dataset_name}):
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

    for (f, t), w in edges.items():
        g.add_edge(f, t, weight=w)

    nx.write_graphml(g, file_name)

def _graph(args):
    return graph(args.dataset, args.outfile)

def configure_parser(subparsers):
    parser = subparsers.add_parser('graph',
                              help='Graph export for OpenSpending datasets')
    parser.add_argument('dataset', help='Dataset name')
    parser.add_argument('outfile', help='File path for GraphML export')
    parser.set_defaults(func=_graph)

