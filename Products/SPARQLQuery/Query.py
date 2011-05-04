from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem

manage_addSPARQLQuery_html = PageTemplateFile('zpt/query_add.zpt', globals())

def manage_addSPARQLQuery(parent, id, title, REQUEST=None):
    """ Create a new SPARQLQuery """
    ob = SPARQLQuery(id, title)
    parent._setObject(id, ob)
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(parent.absolute_url() + '/manage_workspace')

class SPARQLQuery(SimpleItem):
    meta_type = "SPARQL Query"
    manage_options = (
        {'label': 'Edit', 'action': 'manage_edit_html'},
    ) + SimpleItem.manage_options

    security = ClassSecurityInfo()

    query = "QU"

    def __init__(self, id, title):
        super(SPARQLQuery, self).__init__()
        self._setId(id)
        self.title = title

    manage_edit_html = PageTemplateFile('zpt/query_edit.zpt', globals())

    def manage_edit(self, REQUEST):
        """ Edit this query """
        self.title = REQUEST.form['title']
        self.query = REQUEST.form['query']
        REQUEST.RESPONSE.redirect(self.absolute_url() + '/manage_workspace')

InitializeClass(SPARQLQuery)
