import unittest
from mock import Mock, patch
import wsgi_intercept.mechanize_intercept
from zope_wsgi import WsgiApp, css, csstext, parse_html
import mock_db


class BrowserTest(unittest.TestCase):
    def setUp(self):
        from Products.SPARQLQuery.Query import SPARQLQuery

        self.query = SPARQLQuery('sq', "Test Query", "")
        self.query.endpoint_url = "http://cr3.eionet.europa.eu/sparql"
        self.query.query = mock_db.GET_LANG_BY_NAME
        self.query.arguments = u"lang_name:literal"

        self.app = WsgiApp(self.query)

        wsgi_intercept.add_wsgi_intercept('test', 80, lambda: self.app)
        self.browser = wsgi_intercept.mechanize_intercept.Browser()

        self.validate_patch = patch('AccessControl.SecurityManagement'
                                    '.SecurityManager.validate')
        self.validate_patch.start().return_value = True

        self.mock_db = mock_db.MockSparql()
        self.mock_db.start()


    def tearDown(self):
        self.mock_db.stop()
        self.validate_patch.stop()
        wsgi_intercept.remove_wsgi_intercept('test', 80)

    def test_manage_edit(self):
        br = self.browser
        br.open('http://test/manage_edit_html')
        br.select_form(name='edit-query')
        br['title:utf8:ustring'] = "My awesome query"
        br['endpoint_url:utf8:ustring'] = "http://dbpedia.org/sparql"
        br['query:utf8:ustring'] = "New query value"
        br['arguments:utf8:ustring'] = "lang_name:literal:en"
        br.submit()

        self.assertEqual(self.query.title, "My awesome query")
        self.assertEqual(self.query.endpoint_url, "http://dbpedia.org/sparql")
        self.assertEqual(self.query.query, "New query value")
        self.assertEqual(self.query.arguments, "lang_name:literal:en")

    def test_query_test_page(self):
        self.query.query = mock_db.GET_LANG_NAMES
        self.query.arguments = u""
        br = self.browser
        page = parse_html(br.open('http://test/test_html').read())
        table = css(page, 'table.sparql-results')[0]

        table_headings = [e.text for e in css(table, 'thead th')]
        self.assertEqual(table_headings, ['lang_url', 'name'])

        table_data = [[td.text for td in css(tr, 'td')]
                      for tr in css(table, 'tbody tr')]
        self.assertEqual(len(table_data), 45)
        lang_da_url = 'http://rdfdata.eionet.europa.eu/eea/languages/da'
        self.assertEqual(table_data[7], ['<'+lang_da_url+'>', '"Danish"'])

    def test_with_literal_argument(self):
        br = self.browser
        br.open('http://test/test_html')
        br.select_form(name='query-arguments')
        br['lang_name:utf8:ustring'] = "Danish"
        page = parse_html(br.submit().read())

        self.assertEqual(csstext(page, 'table.sparql-results tbody td'),
                         u"<http://rdfdata.eionet.europa.eu/eea/languages/da>")

    def test_REST_query(self):
        from webob import Request
        import sparql
        from Products.SPARQLQuery._depend import json
        from test_query import EIONET_RDF

        req = Request.blank('http://test/?lang_name=Danish')
        response = req.get_response(self.app)

        self.assertEqual(response.headers['Content-Type'], 'application/json')
        json_response = json.loads(response.body)
        danish_iri = sparql.IRI(EIONET_RDF+'/languages/da')
        self.assertEqual(json_response['data'], [[danish_iri.n3()]])
