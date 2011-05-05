import unittest
from mock import patch
from mock_sparql import MockSparql


class QueryTest(unittest.TestCase):
    def setUp(self):
        from Products.SPARQLQuery.Query import SPARQLQuery
        self.query = SPARQLQuery('sq', "Test Query", "_endpoint_")
        self.mock_sparql = MockSparql()
        self.mock_sparql.start()

    def tearDown(self):
        self.mock_sparql.stop()

    def test_simple_query(self):
        from sparql import IRI
        self.query.endpoint_url = "http://cr3.eionet.europa.eu/sparql"
        self.query.query = self.mock_sparql.queries['get_languages']
        result = self.query.execute()
        self.assertEqual(result.fetchall(), [
            (IRI('http://rdfdata.eionet.europa.eu/eea/languages/en'),),
            (IRI('http://rdfdata.eionet.europa.eu/eea/languages/de'),),
        ])

    @patch('Products.SPARQLQuery.Query.threading')
    def test_timeout(self, mock_threading):
        from Products.SPARQLQuery.Query import QueryTimeout
        self.query.endpoint_url = "http://cr3.eionet.europa.eu/sparql"
        self.query.query = self.mock_sparql.queries['get_languages']
        mock_threading.Thread.return_value.isAlive.return_value = True

        self.assertRaises(QueryTimeout, self.query.execute)

    @patch('Products.SPARQLQuery.Query.sparql')
    def test_error(self, mock_sparql):
        self.query.endpoint_url = "http://cr3.eionet.europa.eu/sparql"
        self.query.query = self.mock_sparql.queries['get_languages']
        class MyError(Exception): pass
        mock_sparql.query.side_effect = MyError

        self.assertRaises(MyError, self.query.execute)
