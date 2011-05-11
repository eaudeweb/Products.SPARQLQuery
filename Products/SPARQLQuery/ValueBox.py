from datetime import datetime
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view, view_management_screens
from AccessControl.requestmethod import postonly
from OFS.SimpleItem import SimpleItem
from Products.PythonScripts.PythonScript import PythonScript

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

    security.declareProtected(view, 'value')

    def __init__(self, id, title):
        super(ValueBox, self).__init__()
        self._setId(id)
        self.title = title
        self.update_script = DEFAULT_UPDATE_SCRIPT
        self.value = None

    security.declareProtected(view, 'evaluate')
    def evaluate(self):
        python_script = PythonScript('update_script_runner').__of__(self)
        python_script.write(self.update_script)
        return python_script()

    def pretty_print(self, value):
        import pprint
        return pprint.pformat(value)

    security.declareProtected(view_management_screens, 'manage_update')
    @postonly
    def manage_update(self, REQUEST=None):
        """ Update the boxed value """

        self.value = self.evaluate()

        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_workspace')

    security.declareProtected(view_management_screens, 'manage_edit_html')
    manage_edit_html = PageTemplateFile('zpt/valuebox_edit.zpt', globals())

    security.declareProtected(view_management_screens, 'manage_edit')
    def manage_edit(self, REQUEST):
        """ Edit this value box """
        self.title = REQUEST.form['title']
        self.update_script = REQUEST.form['update_script']
        REQUEST.SESSION['messages'] = ["Saved changes. (%s)" % (datetime.now())]
        REQUEST.RESPONSE.redirect(self.absolute_url() + '/manage_workspace')

    security.declareProtected(view_management_screens, 'manage_preview_html')
    manage_preview_html = PageTemplateFile('zpt/valuebox_preview', globals())

    security.declareProtected(view, 'index_html')
    def index_html(self, REQUEST):
        """ """
        REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
        return self.pretty_print(self.value)

InitializeClass(ValueBox)
