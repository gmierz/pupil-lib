import os
import threading

import numpy as np
from core.utilities.MPLogger import MultiProcessingLog
from core.workers.processors.decorator_registrar import *
# Imports for pre and post processing functions go below this line and above
# the end line below. This is the recommended method of adding new and long
# pre and post processing functions. Import them from the folder and run
# them with some sort of main function. Also, they must only ever accept two
# parameters. Use the config dictionary to modify what you get without
# complicating the code.
#
# --------------------------- Imports start line ----------------------------#
from core.workers.processors.processing_functions.testing_functions import *
from matplotlib import pyplot as plt

from pupillib.core.utilities.utilities import *


# --------------------------- Imports end line ----------------------------#

class TriggerDefaults():
    @staticmethod
    def pre_defaults():
        return []

    @staticmethod
    def post_defaults():
        return [{'name': 'custom_resample', 'config': [{'srate': 256}]},
                {'name': 'rm_baseline', 'config': []},
                {'name': 'get_percent_change', 'config': []}]


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

        # Testing/demo function.
        @pre
        def get_sums(trigger_data, config):
            args = config['config']
            args1 = args[0]['srate']

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

                # Union with all_times, round to 3 decimals to threshold the
                # variability
                all_times = union(all_times, np.around(times, decimals=3))

            # Order all times
            all_times.sort()

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

            # This is the suggested method to use.
            if srate != 'None' and srate is not None:
                print('Resampling trials to ' + str(srate) + 'Hz...')
                new_xrange = np.linspace(all_times[0], all_times[-1], num=srate*(all_times[-1]-all_times[0]))
                for trial_num, trial_info in proc_trial_data.items():
                    trial_info['trial']['data'] = np.interp(new_xrange, trial_info['trial']['timestamps'],
                                                                        trial_info['trial']['data'])
                    trial_info['trial']['timestamps'] = new_xrange
                    checking = trial_info['trial']['timestamps'][-1] - trial_info['trial']['timestamps'][0]
                    if checking != prev_time:
                        logger.send('WARNING', 'Bad time after interpolation, continuing anyway: Got ' +
                                    '%.8f' % checking + ', vs. Expected' + '%.8f' % prev_time,
                                    os.getpid(), threading.get_ident())

            return trigger_data

        # This function should only be run after the
        # custom resampling phase.
        @post
        def rm_baseline(trigger_data, config):
            args = config['config']
            logger = MultiProcessingLog.get_logger()
            testing = trigger_data['config']['testing']
            proc_trial_data = trigger_data['trials']
            new_trial_data = copy.deepcopy(proc_trial_data)
            baseline_range = trigger_data['config']['baseline']

            for trial_num, trial_info in proc_trial_data.items():
                times = copy.deepcopy(trial_info['trial']['timestamps'])
                data = copy.deepcopy(trial_info['trial']['data'])

                # Subtract initial
                times = times - times[0]
                total_time = times[-1]

                # Check to make sure the baseline range is OK.
                if baseline_range[0] < times[0]:
                    raise Exception("Error: Cannot have a negative baseline range start. All trials start at 0. ")
                if baseline_range[1] > total_time:
                    raise Exception("Error: Cannot have a baseline range that exceeds the total time of the trial. ")

                # Get the initial point, then the final point, with all points in
                # between as the baseline mean for each trial.

                bmean = 0
                pcount = 0
                found_first = False
                for time_ind in range(len(times)-1):
                    # While we have not found the first point, continue looking
                    if not found_first:
                        if times[time_ind] <= baseline_range[0] < times[time_ind+1]:
                            pcount += 1
                            if baseline_range[0] == times[time_ind]:
                                bmean += data[time_ind]
                            else:
                                bmean += linear_approx(data[time_ind], times[time_ind],
                                                       data[time_ind+1], times[time_ind+1],
                                                       baseline_range[0])
                            found_first = True
                        continue

                    # Check if we have the final point area, if we do, get it and
                    # finish looking for points.
                    if times[time_ind] <= baseline_range[1] < times[time_ind+1]:
                        pcount += 1
                        if baseline_range[1] == times[time_ind]:
                            bmean += data[time_ind]
                        else:
                            bmean += linear_approx(data[time_ind], times[time_ind],
                                                   data[time_ind + 1], times[time_ind + 1],
                                                   baseline_range[1])
                        break

                    # We get here when we're in between the first and final points.
                    pcount += 1
                    bmean += data[time_ind]

                # For each trial, calculate the baseline removed data and store the baseline mean.
                new_trial_data[trial_num]['baseline_mean'] = bmean/pcount
                new_trial_data[trial_num]['trial_rmbaseline']['data'] = data - new_trial_data[trial_num]['baseline_mean']

            trigger_data['trials'] = new_trial_data

            return trigger_data

        # Calculates the percent change data for each trial.
        @post
        def get_percent_change(trigger_data, config):
            proc_trial_data = trigger_data['trials']
            pcs = {}

            # Get the baseline means if it wasn't already calculated.
            if len(proc_trial_data) > 0:
                for trial_num, trial_info in proc_trial_data.items():
                    if 'baseline_mean' not in trial_info:
                        trigger_data = rm_baseline(trigger_data, {})
                        break
                proc_trial_data = trigger_data['trials']

            for trial_num, trial_info in proc_trial_data.items():
                bmean = trial_info['baseline_mean']
                data = copy.deepcopy(trial_info['trial_rmbaseline']['data'])

                pcs[trial_num] = data/bmean

            for trial_num in pcs:
                trigger_data['trials'][trial_num]['trial_pc']['data'] = pcs[trial_num]

            return trigger_data

        self.pre_processing = pre
        self.post_processing = post
