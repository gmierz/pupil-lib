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
from pupillib.core.workers.processors.decorator_registrar import *

import numpy as np
from pupillib.core.utilities.MPLogger import MultiProcessingLog

# Imports for pre and post processing functions go below this line and above
# the end line below. This is the recommended method of adding new and long
# pre and post processing functions. Import them from the folder and run
# them with some sort of main function. Also, they must only ever accept two
# parameters. Use the config dictionary to modify what you get without
# complicating the code.
#
# --------------------------- Imports start line ----------------------------#
from pupillib.core.workers.processors.processing_functions.testing_functions import *


# --------------------------- Imports end line ----------------------------#

class GenericEyeLevelDefaults():
    @staticmethod
    def pre_defaults():
        return [
            {
                'name': 'tester',
                'config': {}
            }
        ]

    @staticmethod
    def post_defaults():
        return []


class GenericEyeLevelProcessor():
    def __init__(self):
        pre = makeregistrar()
        post = makeregistrar()

        @pre
        def tester(trigger_data, config):
            print('helloooooo')

        @post
        def tester2(trigger_data, config):
            print('done.')

        @post
        def tester3(trigger_data, config):
            a_test_to_do('Print this!')

        self.pre_processing = pre
        self.post_processing = post