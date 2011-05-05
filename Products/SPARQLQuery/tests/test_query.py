import urllib2
from StringIO import StringIO
import unittest
from mock import Mock, patch

SPARQL_GET_LANGS = """\
SELECT ?lang_url WHERE {
  ?lang_url a <http://rdfdata.eionet.europa.eu/eea/ontology/Language> .
}
"""

SPARQL_RESPONSES = {}
SPARQL_RESPONSES[SPARQL_GET_LANGS] = """\
<?xml version='1.0' encoding='UTF-8'?>
<sparql xmlns='http://www.w3.org/2005/sparql-results#'>
	<head>
		<variable name='lang_url'/>
	</head>
	<results>
		<result>
			<binding name='lang_url'>
				<uri>http://rdfdata.eionet.europa.eu/eea/languages/en</uri>
			</binding>
		</result>
		<result>
			<binding name='lang_url'>
				<uri>http://rdfdata.eionet.europa.eu/eea/languages/de</uri>
			</binding>
		</result>
	</results>
</sparql>
"""

def respond_to_sparql(query):
    for key in SPARQL_RESPONSES:
        if query == key.replace("\n", " ").encode('utf-8'):
            return SPARQL_RESPONSES[key]
    else:
        raise ValueError("unknown query: %r" % query)

def mock_urlopen(request):
    try:
        from urlparse import parse_qs
    except ImportError:
        from cgi import parse_qs
    query = parse_qs(request.get_data())['query'][0]

    response = Mock()
    response.fp = StringIO(respond_to_sparql(query))
    return response

class QueryTest(unittest.TestCase):
    def setUp(self):
        from Products.SPARQLQuery.Query import SPARQLQuery
        self.query = SPARQLQuery('sq', "Test Query", "_endpoint_", "_query_")
        self.urllib2_patch = patch('sparql.urllib2')
        mock_urllib2 = self.urllib2_patch.start()
        mock_urllib2.Request = urllib2.Request
        mock_urllib2.urlopen = mock_urlopen

    def tearDown(self):
        self.urllib2_patch.stop()

    def test_simple_query(self):
        from sparql import IRI
        self.query.endpoint_url = "http://cr3.eionet.europa.eu/sparql"
        self.query.query = SPARQL_GET_LANGS
        result = self.query.execute()
        self.assertEqual(result.fetchall(), [
            (IRI('http://rdfdata.eionet.europa.eu/eea/languages/en'),),
            (IRI('http://rdfdata.eionet.europa.eu/eea/languages/de'),),
        ])

    @patch('Products.SPARQLQuery.Query.threading')
    def test_timeout(self, mock_threading):
        from Products.SPARQLQuery.Query import QueryTimeout
        self.query.endpoint_url = "http://cr3.eionet.europa.eu/sparql"
        self.query.query = SPARQL_GET_LANGS
        mock_threading.Thread.return_value.isAlive.return_value = True

        self.assertRaises(QueryTimeout, self.query.execute)

    @patch('Products.SPARQLQuery.Query.sparql')
    def test_error(self, mock_sparql):
        self.query.endpoint_url = "http://cr3.eionet.europa.eu/sparql"
        self.query.query = SPARQL_GET_LANGS
        class MyError(Exception): pass
        mock_sparql.query.side_effect = MyError

        self.assertRaises(MyError, self.query.execute)
