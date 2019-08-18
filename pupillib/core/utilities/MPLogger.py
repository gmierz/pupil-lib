'''
(*)~---------------------------------------------------------------------------
This file is part of Pupil-lib.

Pupil-lib is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Pupil-lib is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Pupil-lib.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2018  Gregory W. Mierzwinski
---------------------------------------------------------------------------~(*)
'''
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

        def __init__(self, logger_type='default', include_threadprocs=False):
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
            self.include_threadprocs = include_threadprocs
            self.logger = logging.getLogger('pupillib')
            self.queue = multiprocessing.Queue(-1)
            self._closing = False

            class Redirector(object):
                def __init__(self, mplogger):
                    self.mplogger = mplogger
                def write(self, msg):
                    if not msg.replace(' ', '').replace('\n', ''):
                        return
                    caller = inspect.getouterframes(inspect.currentframe())[1]
                    self.mplogger.info(msg, caller=caller)
                def flush(self):
                    pass

            self.redirector = Redirector(self)
            sys.stdout = self.redirector

            self.t = threading.Thread(target=self.receive)
            self.t.daemon = True
            self.t.start()

        def enable_redirect(self):
            sys.stdout = self.redirector

        def disable_redirect(self):
            sys.stdout = sys.__stdout__

        def receive(self):
            while (not self._closing) or (not self.queue.empty()):
                if not self.queue.empty():
                    record = self.queue.get()
                    self.logger.log(LOGLEVELS[record.level], record.msg)
                else:
                    continue

        def send(self, level, msg, processid=None, thid=None, caller=None):
            if not processid:
                processid = os.getpid()
            if not thid:
                thid = threading.get_ident()

            try:
                if not caller:
                    caller = inspect.getouterframes(inspect.currentframe())[1]

                repo_path = caller[1]
                repo_path_split = repo_path.split('pupillib')
                if len(repo_path_split) > 1:
                    repo_path = 'pupillib' + repo_path_split[-1]

                out_str = ' - ' + repo_path + ":" + caller[3] + ":" + str(caller[2])
                if self.include_threadprocs:
                    out_str += ' ' + str(processid) + ' ' + str(thid)
                out_str += ' - ' + msg

                self.queue.put_nowait(SimpleRecord(level, out_str))
            except Exception as e:
                self.queue.put_nowait(SimpleRecord('ERROR', 'During message:  ' + msg +
                                                   ' from pid-' + str(processid) + ',thid-' + str(thid) +
                                                   '. \nAn exception occurred: \n' + traceback.format_exc()))

        def close(self):
            self._closing = True
            if self.t.is_alive():
                self.t.join()

        def info(self, msg, processid=None, thid=None, caller=None):
            self.send("INFO", msg, processid=processid, thid=thid, caller=caller)

        def debug(self, msg, processid=None, thid=None):
            self.send("DEBUG", msg, processid=processid, thid=thid)

        def warning(self, msg, processid=None, thid=None):
            self.send("WARNING", msg, processid=processid, thid=thid)

        def error(self, msg, processid=None, thid=None):
            self.send("ERROR", msg, processid=processid, thid=thid)

        def critical(self, msg, processid=None, thid=None):
            self.send("CRITICAL", msg, processid=processid, thid=thid)


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
