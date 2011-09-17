from openspending.lib import solr_util as solr

def load(dataset):
    solr.build_index(dataset)
    return 0

def delete(dataset):
    solr.drop_index(dataset)
    return 0

def optimize():
    solr.optimize()
    return 0

def clean():
    s = solr.get_connection()
    s.delete_query('*:*')
    s.commit()
    return 0

def _load(args):
    return load(args.dataset)

def _delete(args):
    return delete(args.dataset)

def _optimize(args):
    return optimize()

def _clean(args):
    return clean()

def configure_parser(subparsers):
    parser = subparsers.add_parser('solr',
                              help='Solr index operations')
    sp = parser.add_subparsers(title='subcommands')

    p = sp.add_parser('load', help='Load data for dataset into Solr')
    p.add_argument('dataset')
    p.set_defaults(func=_load)

    p = sp.add_parser('delete', help='Delete data for dataset from Solr')
    p.add_argument('dataset')
    p.set_defaults(func=_delete)

    p = sp.add_parser('optimize', help='Optimize the Solr index')
    p.set_defaults(func=_optimize)

    p = sp.add_parser('clean', help='Empty/reset the Solr index')
    p.set_defaults(func=_load)