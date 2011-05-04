from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view_management_screens
from OFS.SimpleItem import SimpleItem

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
        import sparql
        return sparql.query(self.endpoint_url, self.query)

InitializeClass(SPARQLQuery)
