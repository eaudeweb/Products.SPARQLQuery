import sys
from StringIO import StringIO

from ZServer.HTTPResponse import ZServerHTTPResponse
from ZPublisher.Request import Request

from webob import Response
from webob.exc import HTTPNotFound, HTTPSeeOther
from webob.dec import wsgify

def get_zope_request(webob_request):
    outstream = StringIO()
    response = ZServerHTTPResponse(stdout=outstream, stderr=sys.stderr)
    environ = webob_request.environ
    zope_request = Request(environ['wsgi.input'], environ, response)
    zope_request.processInputs()
    return zope_request

class WsgiApp(object):
    """ Horrible hibrid of Zope2 and WSGI, good enough for testing purposes """

    def __init__(self, ui):
        self.ui = ui

    @wsgify
    def __call__(self, request):
        from OFS.Application import Application
        app = Application()

        from ZPublisher.HTTPRequest import HTTPRequest
        app.REQUEST = zope_request = get_zope_request(request)

        try:
            name = request.path[1:] or 'index_html'
            method = getattr(self.ui.__of__(app), name)
        except AttributeError:
            return HTTPNotFound()
        else:
            body = method(zope_request)
            return Response(body)
