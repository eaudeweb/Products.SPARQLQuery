import urllib2
from StringIO import StringIO
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
    query = parse_qs(request.get_data()).get('query', [''])[0]

    response = Mock()
    response.fp = StringIO(respond_to_sparql(query))
    return response

class MockSparql(object):
    queries = {
        'get_languages': SPARQL_GET_LANGS,
    }

    def start(self):
        self.urllib2_patch = patch('sparql.urllib2')
        mock_urllib2 = self.urllib2_patch.start()
        mock_urllib2.Request = urllib2.Request
        mock_urllib2.urlopen = mock_urlopen

    def stop(self):
        self.urllib2_patch.stop()
