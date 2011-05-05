import unittest
from mock import patch
import wsgi_intercept.mechanize_intercept
from zope_wsgi import WsgiApp, css, csstext, parse_html


class BrowserTest(unittest.TestCase):
    def setUp(self):
        from Products.SPARQLQuery.ValueBox import ValueBox

        self.box = ValueBox('box', "Test ValueBox")
        app = WsgiApp(self.box)

        wsgi_intercept.add_wsgi_intercept('test', 80, lambda: app)
        self.browser = wsgi_intercept.mechanize_intercept.Browser()

        self.validate_patch = patch('AccessControl.SecurityManagement'
                                    '.SecurityManager.validate')
        self.validate_patch.start().return_value = True

    def tearDown(self):
        self.validate_patch.stop()
        wsgi_intercept.remove_wsgi_intercept('test', 80)

    def test_manage_edit(self):
        br = self.browser
        br.open('http://test/manage_edit_html')
        br.select_form(name='edit-valuebox')
        br['title:utf8:ustring'] = "My boxed value"
        br.submit()

        self.assertEqual(self.box.title, "My boxed value")
