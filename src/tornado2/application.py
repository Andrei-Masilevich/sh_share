import os
import sys
import signal
import atexit
import logging

from optparse import OptionValueError
import tornado.web
import tornado.ioloop
import tornado.websocket
import tornado.httpserver
from tornado.options import define, options


define("config", type=str, help="Path to config file",
       callback=lambda path: tornado.options.parse_config_file(path,
                                                               final=False))

define("http_port", type=int, default=8080, help="Bind on the given port. From range [1024, 65535]")
define("http_interface", type=str, default="0.0.0.0",
       help="Bind to the given IP interface")
define("debug", type=bool, default=False)
define("pidfile", type=str,
       help="Path to pid file (to control application 'pkill -F')")


class Application(tornado.web.Application):

    @staticmethod
    def check_port():
        if not options.http_port:
            raise OptionValueError("Port is required")
        
        value = int(options.http_port)
        if value not in range(1024, 65535):
            raise OptionValueError(
                "Invalid port value: %r." % (value))
        
        return value
        
    def __init__(self, logger, handlers, **settings):
        self.logger = logger if logger is not None else logging.getLogger()
        if options.debug:
            self.logger.setLevel("DEBUG")
        self.logger.info("Start application")
        self.logger.debug("Debug logging ON")

        self._is_debug = options.debug
        settings['debug'] = self._is_debug
        settings['autoreload'] = self._is_debug

        self.pidfile = options.pidfile
        if self.pidfile:
            pid = str(os.getpid())
            self.logger.info("Write pid %s to %s", pid, self.pidfile)
            open(self.pidfile, 'w').write(pid)

        def signal_handler(signum, frame):
            self.__on_exit()
            sys.exit(0)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        atexit.register(self.__on_exit)

        self.on_cleanup = None
        super(Application, self).__init__(handlers, **settings)

    @property
    def is_debug(self):
        return self._is_debug

    def __on_exit(self):
        try:
            tornado.ioloop.IOLoop.instance().stop()
        except Exception as e:
            self.logger.warning(e)
        finally:
            if self.on_cleanup:
                self.on_cleanup()
                self.on_cleanup = None

    def init(self):
        self.http_server = self.listen(self.check_port(), options.http_interface)
        self.logger.info("Start HTTP server on %d port", options.http_port)
        return self

    def start(self):
        try:
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            tornado.ioloop.IOLoop.instance().stop()
        finally:
            self.logger.info("Stoped application")
            if self.pidfile:
                os.unlink(self.pidfile)
