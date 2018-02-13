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


# --------------------------- Imports end line ----------------------------#

class TrialDefaults():
    @staticmethod
    def pre_defaults():
        return [
            {
                'name': 'None',
                'config': {}
            }
        ]

    @staticmethod
    def post_defaults():
        return [
            {
                'name': 'rm_zero_value_trials',
                'config': [{'zeros_to_count': 1}, {'digit_tolerance': 0}]
            }
        ]


class TrialProcessor():
    def __init__(self):
        pre = makeregistrar()
        post = makeregistrar()

        @pre
        def tester(trial_data, config):
            print('helloooooo')

        @post
        def tester2(trial_data, config):
            print('done.')

        @post
        def tester3(trial_data, config):
            a_test_to_do('Print this!')

        # Removes zero value trials, or trials that have
        # a certain number of zero valued data points seen
        # in a row. This is done by using a rounding
        # tolerance (defaults to 0) for the data points,
        # and a number of times that a data point is seen
        # as zero after rounding (defaults to 1).
        @post
        def rm_zero_value_trials(trial_data, config):
            args = config['config']
            zero_count_tolerance = args[0]['zeros_to_count']
            digit_tolerance = args[1]['digit_tolerance']

            zcount = 0
            throw_away = False
            data = trial_data['trial']['data']
            for i in data:
                if np.round(i, digit_tolerance) == 0:
                    zcount += 1
                    if zcount > zero_count_tolerance:
                        throw_away = True
                        break

            if throw_away:
                trial_data['reject'] = True

            return trial_data

        self.pre_processing = pre
        self.post_processing = post