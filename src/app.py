import os
import re
import sys
import tornado

from optparse import OptionValueError
import os.path as ps
from tornado.options import define, options
from tornado2 import Application, L

from app import HomeHandler, \
                ObjectHandler


define("objects", help="Path to object definitions file in YAML format", 
        type=str, default=ps.join(ps.dirname(__file__), "objects.yaml"))
define("shadow",
        help="Shadow path name to get service. From charset '-._a-z0-9'",
        type=str)
define("share",
        help="Share folder root.",
        type=str)

    
class ShShareApp(Application):

    @staticmethod
    def check_shadow():
        shadow = options.shadow
        if not shadow:
            raise OptionValueError("Shadow is required")
        
        regex = re.compile('^[-._a-z0-9]+$')
        if not re.match(regex, shadow):
            raise OptionValueError(
                "Invalid shadow value: %r." % (shadow))
        
        return shadow
    
    @staticmethod
    def check_share():
        source_folder = options.share
        if not source_folder:
            raise OptionValueError("Shared folder is required")
        
        if not ps.isdir(source_folder):
            raise AssertionError("Invalid share folder %r." % (source_folder))
        
        return source_folder
    
    def __init__(self):
        self.home_url = HomeHandler.URL
        ObjectHandler.URL = self.home_url + options.shadow

        handlers = [
                (r'/favicon.ico',
                    tornado.web.StaticFileHandler,
                    dict(url='/static/favicon.ico', permanent=True)),
                (HomeHandler.URL, HomeHandler)
                    ]

        settings = dict(
            home_url=self.home_url,
            template_path=ps.join(ps.dirname(__file__), "templates"),
            static_path=ps.join(ps.dirname(__file__), "static"),
            default_handler_class=ObjectHandler,
            xsrf_cookies=False
        )

        super().__init__(L, handlers, **settings)


if __name__ == "__main__":
    try:
        tornado.options.parse_command_line()

        app = ShShareApp()
    
        ObjectHandler.init(options.objects, app.check_share(), app.check_shadow())

        app.init()
        
    except OptionValueError as err:
        L.error("Can't load configuration: %s. Use --help option for details.", err)
        sys.exit(1)
    except SystemExit as err:
        sys.exit(err.code)
    except BaseException as err:
        L.error("Can't load configuration: %s.", err)
        sys.exit(2)

    app.start()
    
