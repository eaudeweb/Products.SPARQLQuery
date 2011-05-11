import urllib2
from os import path
from StringIO import StringIO
from mock import Mock, patch

GET_LANGS = """\
SELECT ?lang_url WHERE {
  ?lang_url a <http://rdfdata.eionet.europa.eu/eea/ontology/Language> .
}
"""

GET_LANG_NAMES = """\
PREFIX eea_ontology: <http://rdfdata.eionet.europa.eu/eea/ontology/>
SELECT * WHERE {
  ?lang_url a eea_ontology:Language .
  ?lang_url eea_ontology:name ?name .
  FILTER (lang(?name) = "en") .
}
"""

GET_LANG_BY_NAME = """\
PREFIX eea_ontology: <http://rdfdata.eionet.europa.eu/eea/ontology/>
SELECT * WHERE {
  ?lang_url a eea_ontology:Language .
  ?lang_url eea_ontology:name ${lang_name} .
}
"""

GET_LANG_BY_NAME_DA = GET_LANG_BY_NAME.replace('${lang_name}', '"Danish"')

def pack(q):
    return q.replace("\n", " ").encode('utf-8')

def read_response_xml(name):
    xml_path = path.join(path.dirname(__file__), 'sparql-%s.xml' % name)
    f = open(xml_path, 'rb')
    data = f.read()
    f.close()
    return data

class MockSparql(object):
    queries = {
        pack(GET_LANGS): read_response_xml('get_languages'),
        pack(GET_LANG_NAMES): read_response_xml('get_lang_names'),
        pack(GET_LANG_BY_NAME_DA): read_response_xml('get_lang_by_name-da'),
    }

    def start(self):
        self.urllib2_patch = patch('sparql.urllib2')
        mock_urllib2 = self.urllib2_patch.start()
        mock_urllib2.Request = urllib2.Request
        mock_urllib2.urlopen = self.mock_urlopen

    def stop(self):
        self.urllib2_patch.stop()

    def mock_urlopen(self, request):
        try:
            from urlparse import parse_qs
        except ImportError:
            from cgi import parse_qs
        query = parse_qs(request.get_data()).get('query', [''])[0]

        response = Mock()
        response.fp = StringIO(self.queries[query])
        return response
