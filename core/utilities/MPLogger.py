from logging.handlers import RotatingFileHandler
import multiprocessing
import threading
import logging
import logging.config
import sys
import traceback
import calendar
import time
import inspect
import os
import json


class SimpleRecord:
    def __init__(self, level, msg):
        self.level = level
        self.msg = msg

LOGLEVELS = {
    'CRITICAL': 50,
    'ERROR': 40,
    'WARNING': 30,
    'INFO': 20,
    'DEBUG': 10,
    'NOSET': 0,
}


class MultiProcessingLog:

    class _MultiProcessingLog:

        def __init__(self, logger_type='default'):
            def setup_logging(default_path='logging.json', default_level=logging.INFO, env_key='LOG_CFG'):
                """
                    Setup logging configuration
                """
                path = default_path
                value = os.getenv(env_key, None)
                if value:
                    path = value
                if os.path.exists(path):
                    with open(path, 'rt') as f:
                        config = json.load(f)
                        config['loggers']['']['handlers'] = [str(logger_type)]
                        config['handlers'][logger_type]['level'] = os.environ.get("LOGLEVEL", "NOTSET")
                    logging.config.dictConfig(config)
                else:
                    logging.basicConfig(level=default_level)

            setup_logging(default_path='resources/logger_config.json')
            self.logger = logging.getLogger('MPLogger')
            self.queue = multiprocessing.Queue(-1)
            self._closing = False

            self.t = threading.Thread(target=self.receive)
            self.t.daemon = True
            self.t.start()

        def receive(self):
            while (not self._closing) or (not self.queue.empty()):
                if not self.queue.empty():
                    record = self.queue.get()
                    self.logger.log(LOGLEVELS[record.level], record.msg)
                else:
                    continue

        def send(self, level, msg, processid=os.getpid(), thid=threading.get_ident()):
            try:
                caller = inspect.getouterframes(inspect.currentframe())[1]
                self.queue.put_nowait(SimpleRecord(level, ' - ' + caller[1] + ":" + caller[3] + ":" +
                                                          str(caller[2]) + ' ' + str(processid) + ' ' + str(thid) +
                                                          ' - ' + msg))
            except Exception as e:
                self.queue.put_nowait(SimpleRecord('ERROR', 'During message:  ' + msg +
                                                   ' from pid-' + str(processid) + ',thid-' + str(thid) +
                                                   '. \nAn exception occurred: \n' + traceback.format_exc()))

        def close(self):
            self._closing = True
            if self.t.is_alive():
                self.t.join()


    instance = None

    @staticmethod
    def set_logger_type(logger_type):
        if MultiProcessingLog.instance is None:
            MultiProcessingLog.instance = MultiProcessingLog._MultiProcessingLog(logger_type)
        else:
            MultiProcessingLog.instance.send('WARNING', 'Cannot open a logger of a second type after it has already '
                                                        'been opened.')
        return MultiProcessingLog.instance

    @staticmethod
    def get_logger():
        if MultiProcessingLog.instance is None:
            MultiProcessingLog.instance = MultiProcessingLog._MultiProcessingLog()
        return MultiProcessingLog.instance
