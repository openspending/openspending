# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
This extension makes it easy to edit documentation on GitHub. It is heavily
inspired by the Sphinx extension of exactly the same name in the Astropy
repository:

  https://github.com/astropy/astropy/blob/master/astropy/sphinx/ext/edit_on_github.py

It adds a field to the page template context called ``edit_on_github`` which
can be used to link to the GitHub edit page.

It has the following configuration options (to be set in the project's
``conf.py``):

* `edit_on_github_project`
    The name of the github project, in the form "username/projectname".

* `edit_on_github_branch`
    The name of the branch to edit.  If this is a released version, this should
    be a git tag referring to that version.  For a dev version, it often makes
    sense for it to be "master".  It may also be a git hash.

* `edit_on_github_root_url`
    The root URL of the GitHub instance on which you wish to edit your
    documentation.

* `edit_on_github_doc_root`
    The location within the source tree of the root of the
    documentation source.  Defaults to "doc", but it may make sense to
    set it to "doc/source" if the project uses a separate source
    directory.
"""
import os


def get_url_base(app):
    return '%s/%s/edit/%s/' % (
        app.config.edit_on_github_root_url,
        app.config.edit_on_github_project,
        app.config.edit_on_github_branch)


def html_page_context(app, pagename, templatename, context, doctree):
    if templatename == 'page.html':
        doc_root = app.config.edit_on_github_doc_root
        if doc_root != '' and not doc_root.endswith('/'):
            doc_root += '/'
        doc_path = os.path.relpath(doctree.get('source'), app.builder.srcdir)
        url = get_url_base(app)

        context['edit_on_github'] = url + doc_root + doc_path


def setup(app):
    app.add_config_value('edit_on_github_project', 'REQUIRED', True)
    app.add_config_value('edit_on_github_branch', 'master', True)
    app.add_config_value('edit_on_github_root_url', 'https://github.com', True)
    app.add_config_value('edit_on_github_doc_root', 'doc', True)

    app.connect('html-page-context', html_page_context)
