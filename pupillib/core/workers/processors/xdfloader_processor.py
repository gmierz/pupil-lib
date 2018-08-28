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
import os
import threading

import numpy as np
from pupillib.core.workers.processors.decorator_registrar import *
# Imports for pre and post processing functions go below this line and above
# the end line below. This is the recommended method of adding new and long
# pre and post processing functions. Import them from the folder and run
# them with some sort of main function. Also, they must only ever accept two
# parameters. Use the config dictionary to modify what you get without
# complicating the code.
#
# --------------------------- Imports start line ----------------------------#
from pupillib.core.workers.processors.processing_functions.testing_functions import *

from pupillib.core.utilities.config_store import ConfigStore
from pupillib.core.utilities.MPLogger import MultiProcessingLog


# --------------------------- Imports end line ----------------------------#

class XdfLoaderDefaults():
    @staticmethod
    def defaults():
        return ['tester']


class XdfLoaderProcessor():
    def __init__(self):
        transform = makeregistrar()

        @transform
        def tester(trigger_data, config):
            print('helloooooo')

        @transform
        def get_primitives_column(primitive_entry, config):
            # Given an entry in an xdf data file, like for 'Gaze Primitive Data',
            # get a specified column entry from it.
            col_num = config['num']
            return np.asarray(primitive_entry['time_series'][:, col_num])

        @transform
        def get_pyrep_column(pyrep_entry, config):
            val2get = config['name']
            if 'num' in config:
                num2get = config['num']
                vals = [eval(el[0])[val2get][num2get] for el in pyrep_entry['time_series']]
            else:
                vals = [eval(el[0])[val2get] for el in pyrep_entry['time_series']]
            return np.asarray(vals)

        @transform
        def get_xdf_timestamps(entry, config):
            return np.asarray(list(entry['time_stamps']))

        @transform
        def srate(no_data, config):
            data = config['data']
            ts = config['timestamps']
            return np.size(data, 0) / (np.max(ts) - np.min(ts))

        @transform
        def get_marker_times(marker_entry, config):
            tmp_times = np.asarray(marker_entry['time_stamps'])
            print("Marker times found: " + str(tmp_times))
            return tmp_times

        @transform
        def get_marker_eventnames(marker_entry, config):
            event_names = []
            for event_name in marker_entry['time_series']:
                # Remove the unecessary dimension.
                event_names.append(event_name[0])
            print("Marker events found: " + str(event_names))
            return np.asarray(event_names)

        @transform
        def test_results(data_for_data_name, data_name):
            # Check data fields to make sure they were created and loaded.
            # Skip and warn if we are not testing, otherwise raise and exception.
            testing = ConfigStore.get_instance().frozen_config['testing']
            logger = MultiProcessingLog.get_logger()
            test_pass = True

            if 'data' in data_for_data_name:
                if not data_for_data_name['data'].any():
                    if testing:
                        raise Exception("No data was loaded for the data name entry " + data_name)
                    else:
                        logger.send('WARNING',' Data entry name ' + data_name + ' has no '
                                              'data loaded. Skipping it.',
                                              os.getpid(), threading.get_ident())
                        test_pass = False
            else:
                if testing:
                    raise Exception("No data field was created and loaded for data name entry " + data_name)
                else:
                    logger.send('WARNING', ' Data entry name ' + data_name + ' has no '
                                           'data field created and loaded. Skipping it.',
                                           os.getpid(), threading.get_ident())
                    test_pass = False

            # Check timestamp fields to make sure they were created and loaded.
            # Skip and warn if we are not testing, otherwise raise and exception.
            if 'timestamps' in data_for_data_name:
                if not data_for_data_name['timestamps'].any():
                    if testing:
                        raise Exception("No timestamps were loaded for the data name entry " + data_name)
                    else:
                        logger.send('WARNING', ' Data entry name ' + data_name + ' has no '
                                               'timestamps loaded. Skipping it.',
                                               os.getpid(), threading.get_ident())
                        test_pass = False
            else:
                if testing:
                    raise Exception("No timestamps were created and loaded for data name entry " + data_name)
                else:
                    logger.send('WARNING', ' Data entry name ' + data_name + ' has no '
                                           'timestamps field created and loaded. Skipping it.',
                                           os.getpid(),
                                           threading.get_ident())
                    test_pass = False

            # Check sampling rate fields to make sure they were created and loaded.
            # Skip and warn if we are not testing, otherwise raise and exception.
            if 'srate' in data_for_data_name:
                if not data_for_data_name['srate'].any() or \
                   (isinstance(data_for_data_name['srate'], int) and data_for_data_name['srate'] == 0):
                    if testing:
                        raise Exception("No srate was loaded for the data name entry " + data_name)
                    else:
                        logger.send('WARNING', ' Data entry name ' + data_name + ' has no '
                                               'srate loaded. Skipping it.',
                                               os.getpid(), threading.get_ident())
                        test_pass = False
            else:
                if testing:
                    raise Exception("No srate was created and loaded for data name entry " + data_name)
                else:
                    logger.send('WARNING', ' Data entry name ' + data_name + ' has no '
                                           'srate field created and loaded. Skipping it.',
                                           os.getpid(),
                                           threading.get_ident())
                    test_pass = False
            return test_pass

        self.transform = transform

    def data_name_to_function(self, data_type):
        return {
            # Each of these must always return data, timestamps, and the sampling rate,
            # in that order.
            'eye0': [
                {   # Get data
                    'fn_name': 'get_primitives_column',
                    'field': 'data',
                    'config': {
                        'num': 0
                    }
                },
                {   # Get timestamps
                    'fn_name': 'get_xdf_timestamps',
                    'field': 'timestamps',
                    'config': {
                        'num': 2
                    }
                },
                {   # Get sampling rate
                    'fn_name': 'srate',
                    'field': 'srate',
                    'config': {
                        'data': None,
                        'timestamps': None
                    }
                },
            ],

            'eye1': [
                {  # Get data
                    'fn_name': 'get_primitives_column',
                    'field': 'data',
                    'config': {
                        'num': 0
                    }
                },
                {  # Get timestamps
                    'fn_name': 'get_xdf_timestamps',
                    'field': 'timestamps',
                    'config': {
                        'num': 2
                    }
                },
                {  # Get sampling rate
                    'fn_name': 'srate',
                    'field': 'srate',
                    'config': {
                        'data': None,
                        'timestamps': None
                    }
                },
            ],

            'eye0-pyrep': [
                {  # Get data
                    'fn_name': 'get_pyrep_column',
                    'field': 'data',
                    'config': {
                        'name': 'diameter_3d'
                    }
                },
                {  # Get timestamps
                    'fn_name': 'get_xdf_timestamps',
                    'field': 'timestamps',
                    'config': {
                        'num': 2
                    }
                },
                {  # Get sampling rate
                    'fn_name': 'srate',
                    'field': 'srate',
                    'config': {
                        'data': None,
                        'timestamps': None
                    }
                },
            ],

            'eye1-pyrep': [
                {  # Get data
                    'fn_name': 'get_pyrep_column',
                    'field': 'data',
                    'config': {
                        'name': 'diameter_3d'
                    }
                },
                {  # Get timestamps
                    'fn_name': 'get_xdf_timestamps',
                    'field': 'timestamps',
                    'config': {
                        'num': 2
                    }
                },
                {  # Get sampling rate
                    'fn_name': 'srate',
                    'field': 'srate',
                    'config': {
                        'data': None,
                        'timestamps': None
                    }
                },
            ],

            'gaze_x': [
                {  # Get data
                    'fn_name': 'get_primitives_column',
                    'field': 'data',
                    'config': {
                        'num': 3
                    }
                },
                {  # Get timestamps
                    'fn_name': 'get_xdf_timestamps',
                    'field': 'timestamps',
                    'config': {
                        'num': 2
                    }
                },
                {  # Get sampling rate
                    'fn_name': 'srate',
                    'field': 'srate',
                    'config': {
                        'data': None,
                        'timestamps': None
                    }
                },
            ],

            'gaze_y': [
                {  # Get data
                    'fn_name': 'get_primitives_column',
                    'field': 'data',
                    'config': {
                        'num': 4
                    }
                },
                {  # Get timestamps
                    'fn_name': 'get_xdf_timestamps',
                    'field': 'timestamps',
                    'config': {
                        'num': 2
                    }
                },
                {  # Get sampling rate
                    'fn_name': 'srate',
                    'field': 'srate',
                    'config': {
                        'data': None,
                        'timestamps': None
                    }
                },
            ],

            'gaze_x-pyrep': [
                {  # Get data
                    'fn_name': 'get_pyrep_column',
                    'field': 'data',
                    'config': {
                        'name': 'norm_pos',
                        'num': 0
                    }
                },
                {  # Get timestamps
                    'fn_name': 'get_xdf_timestamps',
                    'field': 'timestamps',
                    'config': {
                        'num': 2
                    }
                },
                {  # Get sampling rate
                    'fn_name': 'srate',
                    'field': 'srate',
                    'config': {
                        'data': None,
                        'timestamps': None
                    }
                },
            ],

            'gaze_y-pyrep': [
                {  # Get data
                    'fn_name': 'get_pyrep_column',
                    'field': 'data',
                    'config': {
                        'name': 'norm_pos',
                        'num': 1
                    }
                },
                {  # Get timestamps
                    'fn_name': 'get_xdf_timestamps',
                    'field': 'timestamps',
                    'config': {
                        'num': 2
                    }
                },
                {  # Get sampling rate
                    'fn_name': 'srate',
                    'field': 'srate',
                    'config': {
                        'data': None,
                        'timestamps': None
                    }
                },
            ]

        }[data_type]
