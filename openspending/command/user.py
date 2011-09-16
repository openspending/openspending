def grant_admin(username):
    from openspending.model import account

    a = account.find_one_by('name', username)

    if a is None:
        print "Account `%s' not found." % username
        return 1

    account.add_role(a, 'admin')

    return 0

def _grant_admin(args):
    return grant_admin(args.username)

def configure_parser(subparsers):
    parser = subparsers.add_parser('user', help='User operations')
    sp = parser.add_subparsers(title='subcommands')

    p = sp.add_parser('grantadmin',
                      help='Grant admin privileges to given user')
    p.add_argument('username')
    p.set_defaults(func=_grant_admin)