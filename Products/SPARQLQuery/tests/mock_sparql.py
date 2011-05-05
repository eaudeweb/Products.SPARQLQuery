import urllib2
from os import path
from StringIO import StringIO
from mock import Mock, patch

SPARQL_GET_LANGS = """\
SELECT ?lang_url WHERE {
  ?lang_url a <http://rdfdata.eionet.europa.eu/eea/ontology/Language> .
}
"""

SPARQL_GET_LANG_NAMES = """\
PREFIX eea_ontology: <http://rdfdata.eionet.europa.eu/eea/ontology/>
SELECT * WHERE {
  ?lang_url a eea_ontology:Language .
  ?lang_url eea_ontology:name ?name .
  FILTER (lang(?name) = "en") .
}
"""

def respond_to_sparql(client_query):
    for name, query in MockSparql.queries.iteritems():
        if client_query == query.replace("\n", " ").encode('utf-8'):
            xml_path = path.join(path.dirname(__file__),
                                 'sparql-%s.xml' % name)
            f = open(xml_path, 'rb')
            data = f.read()
            f.close()
            return data

    else:
        raise ValueError("unknown query: %r" % client_query)

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
        'get_lang_names': SPARQL_GET_LANG_NAMES,
    }

    def start(self):
        self.urllib2_patch = patch('sparql.urllib2')
        mock_urllib2 = self.urllib2_patch.start()
        mock_urllib2.Request = urllib2.Request
        mock_urllib2.urlopen = mock_urlopen

    def stop(self):
        self.urllib2_patch.stop()
