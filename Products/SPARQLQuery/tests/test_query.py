import unittest
from mock import Mock, patch
import mock_db

import sparql

EIONET_RDF = 'http://rdfdata.eionet.europa.eu/eea'

class QueryTest(unittest.TestCase):
    def setUp(self):
        from Products.SPARQLQuery.Query import SPARQLQuery
        self.query = SPARQLQuery('sq', "Test Query", "_endpoint_")
        self.query.endpoint_url = "http://cr3.eionet.europa.eu/sparql"
        self.mock_db = mock_db.MockSparql()
        self.mock_db.start()

    def tearDown(self):
        self.mock_db.stop()

    def test_simple_query(self):
        from sparql import IRI
        self.query.query = mock_db.GET_LANGS
        result = self.query.execute()
        self.assertEqual(result.fetchall(), [
            (IRI(EIONET_RDF + '/languages/en'),),
            (IRI(EIONET_RDF + '/languages/de'),),
        ])

    @patch('Products.SPARQLQuery.Query.threading')
    def test_timeout(self, mock_threading):
        from Products.SPARQLQuery.Query import QueryTimeout
        self.query.query = mock_db.GET_LANGS
        mock_threading.Thread.return_value.isAlive.return_value = True

        self.assertRaises(QueryTimeout, self.query.execute)

    @patch('Products.SPARQLQuery.Query.sparql')
    def test_error(self, mock_sparql):
        self.query.query = mock_db.GET_LANGS
        class MyError(Exception): pass
        mock_sparql.query.side_effect = MyError

        self.assertRaises(MyError, self.query.execute)

    def test_query_with_arguments(self):
        self.query.query = mock_db.GET_LANG_BY_NAME
        result = self.query.execute(lang_name=sparql.Literal("Danish"))

        danish_iri = sparql.IRI(EIONET_RDF+'/languages/da')
        self.assertEqual(list(result), [(danish_iri,)])

    def test_call(self):
        self.assertEqual(self.query.execute, self.query.__call__)


class MapArgumentsTest(unittest.TestCase):

    def _test(self, raw_arg_spec, arg_data, expected):
        from Products.SPARQLQuery.Query import map_arg_values, parse_arg_spec
        missing, result = map_arg_values(parse_arg_spec(raw_arg_spec), arg_data)
        self.assertEqual(missing, [])
        self.assertEqual(result, expected)
        self.assertEqual(map(type, result.values()),
                         map(type, expected.values()))

    def test_map_zero(self):
        self._test(u'', (), {})

    def test_map_one_iri(self):
        en = EIONET_RDF + '/languages/en'
        self._test(u'lang_url:iri',
                   {'lang_url': en},
                   {'lang_url': sparql.IRI(en)})

    def test_map_one_literal(self):
        self._test(u'name:literal',
                   {'name': u"Joe"},
                   {'name': sparql.Literal(u"Joe", None)})

    def test_map_two_values(self):
        en = EIONET_RDF + '/languages/en'
        self._test(u'name:literal lang_url:iri',
                   {'name': u"Joe", 'lang_url': en},
                   {'name': sparql.Literal(u"Joe", None),
                    'lang_url': sparql.IRI(en)})

class InterpolateQueryTest(unittest.TestCase):

    def _test(self, query_spec, var_data, expected):
        from Products.SPARQLQuery.Query import interpolate_query
        result = interpolate_query(query_spec, var_data)
        self.assertEqual(result, expected)

    def test_no_variables(self):
        self._test(u"SELECT * WHERE { ?s ?p ?u }",
                   {},
                   u"SELECT * WHERE { ?s ?p ?u }")

    def test_one_iri(self):
        onto_name = EIONET_RDF + '/ontology/name'
        self._test(u"SELECT * WHERE { ?s ${pred} \"Joe\" }",
                   {'pred': sparql.IRI(onto_name)},
                   u"SELECT * WHERE { ?s <%s> \"Joe\" }" % onto_name)

    def test_one_literal(self):
        self._test(u"SELECT * WHERE { ?s ?p ${value} }",
                   {'value': sparql.Literal("Joe", None)},
                   u"SELECT * WHERE { ?s ?p \"Joe\" }")
