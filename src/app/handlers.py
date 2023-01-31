import json

import tornado.web
import tornado.auth
import tornado
from tornado.options import define, options
from tornado2 import L

from .object_handlers import PingHandler, \
                             ZIPHandler, \
                             ObjectHandler as ObjectHandlerImpl, \
                             init_objects


class BaseHandler(tornado.web.RequestHandler):

    def print_headers(self, headers):
        headers_ = {}
        for (k, v) in headers.get_all():
            headers_[k] = v
        return json.dumps(headers_)

    def write_error(self, status_code, **kwargs):
        # Suppress stack output
        self.write("")


class HomeHandler(BaseHandler):

    URL = r"/"

    def get(self):
        L.debug("GET: %s", self.print_headers(self.request.headers))

        self.render("welcome.html",
                    var_css="simple",
                    var_objects=ObjectHandlerImpl.object_handlers
                    )


class ObjectHandler(BaseHandler):

    URL = None

    @staticmethod
    def init(objects_file, source_folder, shadow):
        init_objects(objects_file, source_folder, shadow)


    def prepare(self):
        if self.request.method == 'HEAD':
            object_handler = ObjectHandlerImpl(self)
            object_handler.do_HEAD()
        elif self.request.method == 'GET':
            object_handler = ObjectHandlerImpl(self)
            object_handler.do_GET()
        else:
            # Log possible malicious activity
            L.warning("%s: %s", self.request.method,
                      self.print_headers(self.request.headers))
    
            self.send_error(406)
