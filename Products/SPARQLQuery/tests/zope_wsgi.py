import sys
from StringIO import StringIO

from ZServer.HTTPResponse import ZServerHTTPResponse
from ZPublisher.Request import Request

from webob import Response
from webob.exc import HTTPNotFound, HTTPForbidden
from webob.dec import wsgify

import lxml.cssselect, lxml.html.soupparser

from mock import Mock

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
        self.session = {}

    @wsgify
    def __call__(self, request):
        from OFS.Application import Application
        app = Application()

        from ZPublisher.HTTPRequest import HTTPRequest
        from zExceptions import Forbidden
        app.REQUEST = zope_request = get_zope_request(request)

        try:
            name = request.path[1:] or 'index_html'
            method = getattr(self.ui.__of__(app), name)
        except AttributeError:
            return HTTPNotFound()
        else:
            headers = {}
            zope_request.RESPONSE.setHeader = Mock(side_effect=headers.__setitem__)
            zope_request.SESSION = self.session
            try:
                body = method(zope_request)
            except Forbidden:
                return HTTPForbidden()
            else:
                return Response(body, headers=headers)


def _register_traversal_adapters():
    # since we're not loading any ZCML, we need to register these adapters
    # by hand.
    from zope.component import getGlobalSiteManager
    gsm = getGlobalSiteManager()
    import zope.traversing.adapters
    gsm.registerAdapter(required=[None],
                        factory=zope.traversing.adapters.Traverser,
                        provided=zope.traversing.interfaces.ITraverser)
    gsm.registerAdapter(required=[None],
                        factory=zope.traversing.adapters.DefaultTraversable,
                        provided=zope.traversing.interfaces.ITraversable)

_register_traversal_adapters()

def css(target, selector):
    return lxml.cssselect.CSSSelector(selector)(target)

def csstext(target, selector):
    return ' '.join(e.text_content() for e in css(target, selector)).strip()

def parse_html(html):
    return lxml.html.soupparser.fromstring(html)
