from core.workers.processors.decorator_registrar import *
from core.utilities.utilities import *
from core.utilities.MPLogger import MultiProcessingLog
from matplotlib import pyplot as plt
import numpy as np
import os
import threading

# Imports for pre and post processing functions go below this line and above
# the end line below. This is the recommended method of adding new and long
# pre and post processing functions. Import them from the folder and run
# them with some sort of main function. Also, they must only ever accept two
# parameters. Use the config dictionary to modify what you get without
# complicating the code.
#
# --------------------------- Imports start line ----------------------------#
from core.workers.processors.processing_functions.testing_functions import *


# --------------------------- Imports end line ----------------------------#

class TriggerDefaults():
    @staticmethod
    def pre_defaults():
        return []

    @staticmethod
    def post_defaults():
        return [{'name': 'custom_resample', 'config': [{'srate': 256}]}]


class TriggerProcessor():
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

        @pre
        def get_sums(trigger_data, config):
            args = config['config']
            args1 = args[0]

            print('get_sums got: ' + str(args1))
            print('Result: ' + str(int(args1) + 10))

            return trigger_data

        # This function resamples all the trials
        # to a common set of time points. By default,
        # we resample to the highest number of points
        # in a single trial. If a sampling rate is specified
        # then we resample it to that level also. We only use
        # linear resampling.
        # TODO:
        # Allow customized interpolation.
        @post
        def custom_resample(trigger_data, config):
            args = config['config']
            logger = MultiProcessingLog.get_logger()
            testing = trigger_data['config']['testing']

            # Get srate
            srate = args[0]['srate']

            # Get all times to find points at:
            # Subtract initial value to normalize to trial range,
            # then union all time sets to remove duplicates, and
            # finally order them.
            proc_trial_data = trigger_data['trials']
            all_times = []
            prev_time = 0
            first = True
            for trial_num, trial_info in proc_trial_data.items():
                times = copy.deepcopy(trial_info['trial']['timestamps'])
                first_val = times[0]

                # Subtract initial
                times = times - first_val
                total_time = times[-1]

                if not first:
                    if total_time != prev_time:
                        logger.send('ERROR', 'Trials do not have matching times, will not continue processing- ' +
                                         'got: ' + str(total_time) + ', exp: ' + str(prev_time), os.getpid(),
                                         threading.get_ident())
                        raise Exception('ERROR: Time mismatch error.')
                else:
                    first = False
                    prev_time = total_time
                print('times')
                print(len(times))

                # Union with all_times, round to 3 decimals to threshold the
                # variability
                all_times = union(all_times, np.around(times, decimals=3))

            # Order all times
            all_times.sort()
            print('all_times')
            print(len(all_times))

            for trial_num, trial_info in proc_trial_data.items():
                old_data = copy.deepcopy(trial_info['trial']['data'])
                old_times = copy.deepcopy(trial_info['trial']['timestamps'])
                old_times = old_times-old_times[0]

                trial_info['trial']['data'] = np.interp(all_times, old_times, old_data)
                trial_info['trial']['timestamps'] = all_times

                if testing:
                    plt.figure()
                    plt.plot(old_times, old_data)
                    plt.plot(all_times, trial_info['trial']['data'])
                    plt.show()

            if srate != 'None' and srate is not None:
                print('Resampling trials to ' + str(srate) + 'Hz...')
                new_xrange = np.linspace(all_times[0], all_times[-1], num=srate*(all_times[-1]-all_times[0]))
                for trial_num, trial_info in proc_trial_data.items():
                    trial_info['trial']['data'] = np.interp(new_xrange, trial_info['trial']['timestamps'],
                                                                        trial_info['trial']['data'])
            return trigger_data

        @post
        def rm_baseline(trigger_data, config):
            args = config['config']
            logger = MultiProcessingLog.get_logger()
            testing = trigger_data['config']['testing']
            proc_trial_data = trigger_data['trials']

            if proc_trial_data['config']['contains_marker']:
                return trigger_data
            else:
                return trigger_data

        self.pre_processing = pre
        self.post_processing = post
