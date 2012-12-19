import logging
import os
import json
import hashlib
import urllib

from pylons import config

from openspending.model import Dataset, Source, meta as db

log = logging.getLogger(__name__)


def file_name(path, source):
    file_name = hashlib.sha1(source.url).hexdigest()[:10]
    file_name += '-' + os.path.basename(source.url)
    return os.path.join(path, file_name)


def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def update_source(archive_dir, source):
    if source.dataset is None:
        continue
    fname = file_name(archive_dir, source)
    fname_tmp = fname + '.tmp'
    log.info("Fetching %s to %s", source.url, fname)
    if not os.path.isfile(fname):
        try:
            (fn, headers) = urllib.urlretrieve(source.url, fname_tmp)
            os.rename(fname_tmp, fname)
        except Exception, e:
            log.exception(e)
    if os.path.isfile(fname):
        log.info("OK: %s", sizeof_fmt(os.path.getsize(fname)))


def update(archive_dir):
    if not os.path.isdir(archive_dir):
        os.makedirs(archive_dir)
    for source in Source.all():
        update_source(archive_dir, source)


def _update(args):
    return update(args.archive_dir)


def configure_parser(subparsers):
    parser = subparsers.add_parser('archive', help='Archival of source data')
    sp = parser.add_subparsers(title='subcommands')

    p = sp.add_parser('update',
                      help='Create a source data archive')
    p.add_argument('archive_dir', help="Archive folder path")    
    p.set_defaults(func=_update)


