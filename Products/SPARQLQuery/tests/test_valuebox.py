import unittest
from mock import patch
import wsgi_intercept.mechanize_intercept
from zope_wsgi import WsgiApp, css, csstext, parse_html


class ValueBoxApiTest(unittest.TestCase):
    def setUp(self):
        from Products.SPARQLQuery.ValueBox import ValueBox
        self.box = ValueBox('box', "Test ValueBox")

    def test_evaluate_ok(self):
        self.box.update_script = "return '%.2f' % 1.2345\n"
        result1 = self.box.evaluate()
        self.assertEqual(result1, '1.23')

        self.box.update_script = "return {1: None, '2': [7,8]}\n"
        result2 = self.box.evaluate()
        self.assertEqual(result2, {1: None, '2': [7,8]})

    def test_evaluate_unauthorized(self):
        from AccessControl import Unauthorized
        self.box.update_script = "import os; os.system('/bin/ls')"
        self.assertRaises(Unauthorized, self.box.evaluate)

    def test_exception(self):
        self.box.update_script = "raise ValueError('hello world')"
        try:
            self.box.evaluate()
        except ValueError, e:
            self.assertEqual(e.args, ('hello world',))
        else:
            self.fail("ValueError not raised")


class ValueBoxBrowserTest(unittest.TestCase):
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
        br['update_script:utf8:ustring'] = "return '%.2f' % 1.2345\n"
        br.submit()

        self.assertEqual(self.box.title, "My boxed value")
        self.assertEqual(self.box.update_script, "return '%.2f' % 1.2345\n")

    def test_update_preview(self):
        self.box.update_script = "return '%.2f' % 1.2345\n"
        br = self.browser
        page = parse_html(br.open('http://test/manage_preview').read())
        self.assertEqual(csstext(page, 'div.update-preview'), "1.23")
