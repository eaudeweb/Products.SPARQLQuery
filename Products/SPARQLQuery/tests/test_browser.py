import unittest
from mock import Mock, patch
import wsgi_intercept.mechanize_intercept
from zope_wsgi import WsgiApp
from mock_sparql import MockSparql


def css(target, selector):
    from lxml.cssselect import CSSSelector
    return CSSSelector(selector)(target)

def csstext(target, selector):
    return ' '.join(e.text_content() for e in css(target, selector)).strip()

def parse_html(html):
    from lxml.html.soupparser import fromstring
    return fromstring(html)

class BrowserTest(unittest.TestCase):
    def setUp(self):
        from Products.SPARQLQuery.Query import SPARQLQuery

        self.query = SPARQLQuery('sq', "Test Query", "")
        app = WsgiApp(self.query)

        wsgi_intercept.add_wsgi_intercept('test', 80, lambda: app)
        self.browser = wsgi_intercept.mechanize_intercept.Browser()

        self.validate_patch = patch('AccessControl.SecurityManagement'
                                    '.SecurityManager.validate')
        self.validate_patch.start().return_value = True

        self.mock_sparql = MockSparql()
        self.mock_sparql.start()


    def tearDown(self):
        self.mock_sparql.stop()
        self.validate_patch.stop()
        wsgi_intercept.remove_wsgi_intercept('test', 80)

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

    def test_index(self):
        self.query.endpoint_url = "http://cr3.eionet.europa.eu/sparql"
        self.query.query = self.mock_sparql.queries['get_lang_names']
        br = self.browser
        page = parse_html(br.open('http://test/').read())
        table = css(page, 'table.sparql-results')[0]

        table_headings = [e.text for e in css(table, 'thead th')]
        self.assertEqual(table_headings, ['lang_url', 'name'])

        table_data = [[td.text for td in css(tr, 'td')]
                      for tr in css(table, 'tbody tr')]
        self.assertEqual(len(table_data), 45)
        lang_da_url = 'http://rdfdata.eionet.europa.eu/eea/languages/da'
        self.assertEqual(table_data[7], ['<'+lang_da_url+'>', '"Danish"'])
