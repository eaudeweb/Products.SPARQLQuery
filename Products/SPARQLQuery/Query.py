import sys
import threading
from time import time
from _depend import json
from datetime import datetime

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view, view_management_screens
from OFS.SimpleItem import SimpleItem

import sparql

class QueryTimeout(Exception):
    pass

manage_addSPARQLQuery_html = PageTemplateFile('zpt/query_add.zpt', globals())

def manage_addSPARQLQuery(parent, id, title, endpoint_url="", REQUEST=None):
    """ Create a new SPARQLQuery """
    ob = SPARQLQuery(id, title, endpoint_url)
    parent._setObject(id, ob)
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(parent.absolute_url() + '/manage_workspace')

class SPARQLQuery(SimpleItem):
    meta_type = "SPARQL Query"
    manage_options = (
        {'label': 'Edit', 'action': 'manage_edit_html'},
        {'label': 'Test', 'action': 'test_html'},
    ) + SimpleItem.manage_options

    security = ClassSecurityInfo()

    __ac_permissions__ = (
        # security.declareProtected does not seem to work on __call__
        ('View', ('__call__','')),
    )

    def __init__(self, id, title, endpoint_url):
        super(SPARQLQuery, self).__init__()
        self._setId(id)
        self.title = title
        self.endpoint_url = endpoint_url
        self.timeout = None
        self.arg_spec = ""
        self.query = ""

    security.declareProtected(view_management_screens, 'manage_edit_html')
    manage_edit_html = PageTemplateFile('zpt/query_edit.zpt', globals())

    security.declareProtected(view_management_screens, 'manage_edit')
    def manage_edit(self, REQUEST):
        """ Edit this query """
        self.title = REQUEST.form['title']
        self.endpoint_url= REQUEST.form['endpoint_url']
        timeout = REQUEST.form['timeout'] or None
        if timeout is not None:
            timeout = float(timeout)
        self.timeout = timeout
        self.query = REQUEST.form['query']
        self.arg_spec = REQUEST.form['arg_spec']
        REQUEST.SESSION['messages'] = ["Saved changes. (%s)" % (datetime.now())]
        REQUEST.RESPONSE.redirect(self.absolute_url() + '/manage_workspace')

    security.declareProtected(view, 'execute')
    def execute(self, **arg_values):
        cooked_query = interpolate_query(self.query, arg_values)
        args = (self.endpoint_url, cooked_query)
        return run_with_timeout(self.timeout, sparql.query, *args)

    # __call__ requires the "View" permission, see __ac_permissions__ above.
    __call__ = execute

    _test_html = PageTemplateFile('zpt/query_test.zpt', globals())

    def index_html(self, REQUEST=None, **kwargs):
        """
        REST API

        Request format is the same as for the `test_html` method.

        Response will be JSON, with values encoded as strings in N3 format.
        """

        if REQUEST is not None:
            kwargs.update(REQUEST.form)

        arg_values = self.map_arguments(**kwargs)
        result = self.execute(**arg_values)

        response = {'data': list(result)}
        if REQUEST is not None:
            REQUEST.RESPONSE.setHeader('Content-Type', 'application/json')
        return json.dumps(response, default=rdf_values_to_json)

    security.declareProtected(view, 'map_arguments')
    def map_arguments(self, **kwargs):
        """ Map the given arguments to our arg_spec """
        arg_spec = parse_arg_spec(self.arg_spec)
        missing, arg_values = map_arg_values(arg_spec, kwargs)
        if missing:
            raise KeyError("Missing arguments: %r" % missing)
        else:
            return arg_values

    security.declareProtected(view, 'map_and_execute')
    def map_and_execute(self, **kwargs):
        """
        Map the given arguments to our arg_spec and execute the query.
        `query.map_and_execute(**data)` is exactly equivalent to
        `query.execute(**query.map_arguments(**data))`.
        """
        return self.execute(**self.map_arguments(**kwargs))

    security.declareProtected(view, 'test_html')
    def test_html(self, REQUEST):
        """
        Execute the query and pretty-print the results as an HTML table.
        """

        arg_spec = parse_arg_spec(self.arg_spec)
        missing, arg_values = map_arg_values(arg_spec, REQUEST.form)
        error = None

        if missing:
            # missing argument
            data = None
            dt = 0

        else:
            t0 = time()

            try:
                result = self.execute(**arg_values)

            except Exception, e:
                import traceback
                error = traceback.format_exc()
                data = None

            else:
                data = {
                    'var_names': [unicode(name) for name in result.variables],
                    'rows': result.fetchall(),
                }

            dt = time() - t0

        options = {
            'query': interpolate_query_html(self.query, arg_values),
            'data': data,
            'duration': dt,
            'arg_spec': arg_spec,
            'error': error,
        }
        return self._test_html(REQUEST, **options)

InitializeClass(SPARQLQuery)


def run_with_timeout(timeout, func, *args, **kwargs):
    """
    Run the given callable in a separate thread; if it does not return within
    `timeout` seconds, ignore the result and raise `QueryTimeout`.
    """

    result = {}
    def thread_job():
        try:
            ret = func(*args, **kwargs)
        except Exception, e:
            result['exception'] = sys.exc_info()
        else:
            result['return'] = ret

    worker = threading.Thread(target=thread_job)
    worker.start()
    worker.join(timeout)
    if worker.isAlive():
        raise QueryTimeout

    if 'exception' in result:
        exc_info = result['exception']
        raise exc_info[0], exc_info[1], exc_info[2]
    else:
        return result['return']

RDF_TERM_FACTORY = {
    'n3term':   sparql.parse_n3_term,
    'iri':      sparql.IRI,
    'string':   sparql.Literal,
    'integer':  lambda v: sparql.TypedLiteral(v, sparql.XSD_INTEGER),
    'long':     lambda v: sparql.TypedLiteral(v, sparql.XSD_LONG),
    'double':   lambda v: sparql.TypedLiteral(v, sparql.XSD_DOUBLE),
    'float':    lambda v: sparql.TypedLiteral(v, sparql.XSD_FLOAT),
    'decimal':  lambda v: sparql.TypedLiteral(v, sparql.XSD_DECIMAL),
    'datetime': lambda v: sparql.TypedLiteral(v, sparql.XSD_DATETIME),
    'date':     lambda v: sparql.TypedLiteral(v, sparql.XSD_DATE),
    'time':     lambda v: sparql.TypedLiteral(v, sparql.XSD_TIME),
    'boolean':  lambda v: sparql.TypedLiteral(v, sparql.XSD_BOOLEAN),
}

def parse_arg_spec(raw_arg_spec):
    arg_spec = {}
    for one_arg_spec in raw_arg_spec.split():
        name, type_spec = one_arg_spec.split(':')
        factory = RDF_TERM_FACTORY[type_spec]
        arg_spec[str(name)] = factory
    return arg_spec

def map_arg_values(raw_arg_spec, arg_data):
    arg_values = {}
    missing = []
    for name, factory in raw_arg_spec.iteritems():
        if name in arg_data:
            arg_values[name] = factory(arg_data[name])
        else:
            missing.append(name)

    return missing, arg_values

def interpolate_query(query_spec, var_data):
    from string import Template
    var_strings = dict( (k, v.n3()) for (k, v) in var_data.iteritems() )
    return Template(query_spec).substitute(**var_strings)

def html_quote(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def interpolate_query_html(query_spec, var_data):
    """
    Debugging version of interpolate_query. The result is a SPARQL query
    that contains HTML markup highlighting where variable substitutions take
    place.
    """
    from string import Template
    var_strings = dict( (k, v.n3()) for (k, v) in var_data.iteritems() )
    tmpl = Template(html_quote(query_spec))
    def convert(mo): # Simplified version of Template's helper function
        named = mo.group('named') or mo.group('braced')
        if named is not None:
            css_class = ['variable']
            if named in var_strings:
                css_class.append('interpolated')
                text = var_strings[named]
            else:
                text = mo.group()
            return '<span class="%(css_class)s">%(text)s</span>' % {
                'css_class': ' '.join(css_class),
                'text': html_quote(text),
            }
            # TODO return '%s' % var_strings.get(named, mo.group())
        if mo.group('escaped') is not None:
            return tmpl.delimiter
        if mo.group('invalid') is not None:
            tmpl._invalid(mo)
        raise ValueError('Unrecognized named group in pattern', tmpl.pattern)
    return tmpl.pattern.sub(convert, tmpl.template)

def rdf_values_to_json(value):
    if isinstance(value, sparql.RDFTerm):
        return value.n3()
    raise TypeError
