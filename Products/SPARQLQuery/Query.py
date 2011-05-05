import sys
import threading
from time import time

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens
from OFS.SimpleItem import SimpleItem

import sparql

class QueryTimeout(Exception):
    pass

manage_addSPARQLQuery_html = PageTemplateFile('zpt/query_add.zpt', globals())

def manage_addSPARQLQuery(parent, id, title, query="", endpoint_url="",
                          REQUEST=None):
    """ Create a new SPARQLQuery """
    ob = SPARQLQuery(id, title, query, endpoint_url)
    parent._setObject(id, ob)
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(parent.absolute_url() + '/manage_workspace')

class SPARQLQuery(SimpleItem):
    meta_type = "SPARQL Query"
    manage_options = (
        {'label': 'Edit', 'action': 'manage_edit_html'},
        {'label': 'View', 'action': 'index_html'},
    ) + SimpleItem.manage_options

    security = ClassSecurityInfo()

    def __init__(self, id, title, query, endpoint_url):
        super(SPARQLQuery, self).__init__()
        self._setId(id)
        self.title = title
        self.query = query
        self.endpoint_url = endpoint_url

    security.declareProtected(view_management_screens, 'manage_edit_html')
    manage_edit_html = PageTemplateFile('zpt/query_edit.zpt', globals())

    security.declareProtected(view_management_screens, 'manage_edit')
    def manage_edit(self, REQUEST):
        """ Edit this query """
        self.title = REQUEST.form['title']
        self.endpoint_url= REQUEST.form['endpoint_url']
        self.query = REQUEST.form['query']
        REQUEST.RESPONSE.redirect(self.absolute_url() + '/manage_workspace')

    def execute(self):
        return run_with_timeout(5, sparql.query, self.endpoint_url, self.query)


    render_results = PageTemplateFile('zpt/query_results.zpt', globals())

    def index_html(self, REQUEST):
        """ execute the query """
        t0 = time()
        result = self.execute()
        dt = time() - t0
        data = {
            'query_duration': dt,
            'var_names': [unicode(name) for name in result.variables],
            'rows': result.fetchall(),
        }
        options = {
            'query': self.query,
            'data': data,
            'duration': dt,
        }
        return self.render_results(REQUEST, **options)

InitializeClass(SPARQLQuery)


def run_with_timeout(timeout, func, *args, **kwargs):
    result = {}
    def thread_job():
        try:
            ret = func(*args, **kwargs)
        except Exception, e:
            result['exception'] = sys.exc_info()
        else:
            result['return'] = ret

    worker = threading.Thread(target=thread_job)
    worker.start()
    worker.join(timeout)
    if worker.isAlive():
        raise QueryTimeout

    if 'exception' in result:
        exc_info = result['exception']
        raise exc_info[0], exc_info[1], exc_info[2]
    else:
        return result['return']
