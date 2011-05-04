import unittest
from mock import Mock
from zope_wsgi import WsgiApp

def csstext(target, selector):
    from lxml.cssselect import CSSSelector
    return ' '.join(e.text_content() for e in
                    CSSSelector(selector)(target)).strip()

def parse_html(html):
    from lxml.html.soupparser import fromstring
    return fromstring(html)

class BrowserTest(unittest.TestCase):
    def setUp(self):
        from Products.SPARQLQuery.Query import SPARQLQuery

        self.query = SPARQLQuery('sq', "Test Query", "", "")
        app = WsgiApp(self.query)

        import wsgi_intercept.mechanize_intercept
        wsgi_intercept.add_wsgi_intercept('test', 80, lambda: app)
        self.browser = wsgi_intercept.mechanize_intercept.Browser()

        import AccessControl
        sm = AccessControl.SecurityManagement.SecurityManager
        sm.validate = lambda *args, **kwargs: True

    def tearDown(self):
        import wsgi_intercept
        wsgi_intercept.remove_wsgi_intercept('test', 80)
        pass

    def test_manage_edit(self):
        br = self.browser
        br.open('http://test/manage_edit_html')
        br.select_form(name='edit-query')
        br['title:utf8:ustring'] = "My awesome query"
        br['endpoint_url:utf8:ustring'] = "http://dbpedia.org/sparql"
        br['query:utf8:ustring'] = "New query value"
        br.submit()

        self.assertEqual(self.query.title, "My awesome query")
        self.assertEqual(self.query.endpoint_url, "http://dbpedia.org/sparql")
        self.assertEqual(self.query.query, "New query value")
