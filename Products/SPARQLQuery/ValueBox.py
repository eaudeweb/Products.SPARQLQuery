from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view, view_management_screens
from OFS.SimpleItem import SimpleItem

DEFAULT_UPDATE_SCRIPT = """\
# This script is run to update the boxed value.
"""

manage_addValueBox_html = PageTemplateFile('zpt/valuebox_add.zpt', globals())

def manage_addValueBox(parent, id, title, REQUEST=None):
    """ Create a new ValueBox """
    ob = ValueBox(id, title)
    parent._setObject(id, ob)
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(parent.absolute_url() + '/manage_workspace')

class ValueBox(SimpleItem):
    meta_type = "Value Box"
    manage_options = (
        {'label': 'Edit', 'action': 'manage_edit_html'},
        {'label': 'View', 'action': 'index_html'},
    ) + SimpleItem.manage_options

    security = ClassSecurityInfo()

    def __init__(self, id, title):
        super(ValueBox, self).__init__()
        self._setId(id)
        self.title = title
        self.update_script = DEFAULT_UPDATE_SCRIPT

    security.declareProtected(view_management_screens, 'manage_edit_html')
    manage_edit_html = PageTemplateFile('zpt/valuebox_edit.zpt', globals())

    security.declareProtected(view_management_screens, 'manage_edit')
    def manage_edit(self, REQUEST):
        """ Edit this value box """
        self.title = REQUEST.form['title']
        self.update_script = REQUEST.form['update_script']
        REQUEST.RESPONSE.redirect(self.absolute_url() + '/manage_workspace')

    security.declareProtected(view, 'index_html')
    def index_html(self, REQUEST):
        """ """
        return "hi"

InitializeClass(ValueBox)
