import logging
import os
import posixpath
import json
import hashlib
import urllib
from flask.ext.script import prompt_bool

from openspending.model import Dataset, Source
from openspending.command.util import create_submanager
from openspending.command.util import CommandException


log = logging.getLogger(__name__)
manager = create_submanager(description='Archival of source data')


def get_url_filename(url):
    """
    Get a base filename for a url. Returns short hashed url appended by the
    urn filename (basefile)
    """

    # Return the first 10 hexdigest chars of sha1 appended by the basename
    # we use posixpath so that getting the basename of the url will work on
    # non-unix (posix-compliant) systems as well
    return '-'.join([hashlib.sha1(url).hexdigest()[:10],
                     posixpath.basename(url)])


def file_name(path, source):
    """
    Return a filename based on the source url located at the relative or
    absolute path provided
    """

    file_name = get_url_filename(source.url)
    return os.path.join(path, file_name)


def sizeof_fmt(num):
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def update_source(archive_dir, source):
    if source.dataset is None:
        return
    fname = file_name(archive_dir, source)
    fname_tmp = fname + '.tmp'
    log.info("Fetching %s to %s", source.url, fname)
    if not os.path.isfile(fname):
        try:
            urllib.urlretrieve(source.url, fname_tmp)
            os.rename(fname_tmp, fname)
        except Exception as e:
            log.exception(e)
    if os.path.isfile(fname):
        log.info("OK: %s", sizeof_fmt(os.path.getsize(fname)))


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


@manager.command
@manager.option("archive_dir", help="Archive folder path")
def update(archive_dir, dataset=None):
    """ Create a source data archive. """
    # Download all sources into an archive directory. If dataset parameter
    #is provided only sources for that dataset will be fetched (otherwise
    # all source in the database will be fetched)
    
    # Create archive directory if it doesn't exist
    if not os.path.isdir(archive_dir):
        os.makedirs(archive_dir)

    # If a dataset is provided we limit to only its sources (else we take all)
    sources = Source.all() if dataset is None else dataset.sources

    # Update each source
    for source in sources:
        update_source(archive_dir, source)


def archive_model(dataset, archive_dir):
    """
    Archive the dataset model (sources, views, mapping, dataset metadata)
    and put it into model.json in the archive directory
    """

    # Create the dataset model (returns a dict with keys: mapping and dataset)
    model = dataset.model_data
    # Add sources to the dataset metadata
    model['dataset']['sources'] = [s.url for s in dataset.sources]

    # Let user know we're about to create model.json
    log.info("Creating %s/model.json for %s", archive_dir, dataset.name)

    # Write the result to a file
    with open(os.path.join(archive_dir, 'model.json'), 'w') as fh:
        fh.write(json.dumps(model, indent=2, default=date_handler))


def archive_visualisations(dataset, archive_dir):
    """
    Archive the visualisations for a dataset and put it into a special
    visualisations.json file in the archive directory
    """

    visualisations = {'visualisations': [v.as_dict() for v in dataset.views]}
    log.info('Creating %s/visualisations.json for %s',
             archive_dir, dataset.name)

    # Write the result to a file
    with open(os.path.join(archive_dir, 'visualisations.json'), 'w') as fh:
        fh.write(json.dumps(visualisations, indent=2, default=date_handler))


@manager.command
@manager.option("archive_dir", help="Archive folder path")
def one(dataset_name, archive_dir):
    """ Archive a single dataset """
    # Find the dataset, create the archive directory and start archiving
    
    # Find the dataset
    dataset = Dataset.by_name(dataset_name)
    # If no dataset found, exit with error message
    if dataset is None:
        raise CommandException("Dataset not found. Unable to archive it.")

    # If the archive_dir exists we have to ask the user if we should overwrite
    if os.path.exists(archive_dir):
        # If user doesn't want to write over it we exit
        if not prompt_bool("%s exists. Overwrite?" % archive_dir):
            return
    
    # If the archive dir is a file we don't do anything
    if os.path.isfile(archive_dir):
        raise CommandException("Cannot overwrite a file (need a directory).")

    # If the archive_dir doesn't exist we create it
    else:
        try:
            os.makedirs(archive_dir)
        except OSError:
            # If we couldn't create it, we exit with an error message
            raise CommandException("Couldn't create archive directory.")

    # Archive the model (dataset metadata)
    archive_model(dataset, archive_dir)
    # Archive the visualisations
    archive_visualisations(dataset, archive_dir)
    # Download all sources
    update(os.path.join(archive_dir, 'sources'), dataset)
