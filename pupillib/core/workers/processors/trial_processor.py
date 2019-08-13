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
import numpy as np
import copy

from pupillib.core.utilities.MPLogger import MultiProcessingLog
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
            #{
            #    'name': 'rm_zero_value_trials',
            #    'config': [{'zeros_to_count': 4}, {'digit_tolerance': 0}]
            #},
            #{
            #    'name': 'filter_moving_average',
            #    'config': [{'window_size': 5}]
            #},
            {
                'name': 'filter_fft',
                'config': [{'highest_freq': 2}, {'lowest_freq': 0}]
            }
        ]


def filter_fft_data(data, low_freq, high_freq, srate):
    dist_between_samples = 1 / srate

    # Bad hack to deal with the windowing and edge effects
    # TODO: Make this function lose data on it's edges
    # TODO: or leave it alone.
    init_length = len(data)
    pad_data = np.concatenate(
        [
            data[0:int(len(data) / 2)][::-1],
            data,
            data[int(len(data) / 2):][::-1]
        ]
    )

    freq_bins = np.fft.fftfreq(pad_data.size, d=dist_between_samples)
    freq_signal = np.fft.fft(pad_data, n=len(pad_data))

    filt_freq_signal = freq_signal.copy()
    zero_freq = copy.deepcopy(filt_freq_signal[freq_bins == 0])
    filt_freq_signal[(abs(freq_bins) < low_freq)] = 0
    filt_freq_signal[(abs(freq_bins) > high_freq)] = 0
    filt_freq_signal[freq_bins == 0] = zero_freq

    start = int(init_length / 2)
    filt_signal = np.fft.ifft(filt_freq_signal, n=len(pad_data)).real
    filt_signal = filt_signal[start:start + init_length]
    return filt_signal


def filter_rm_trials_with_vals_gt(data, gtval):
    maxdata = max(data)
    if maxdata >= gtval:
        return True
    return False


def filter_rm_trials_with_vals_lt(data, ltval):
    mindata = min(data)
    if mindata <= ltval:
        return True
    return False

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
        #
        # Example usage in post_defaults above:
        #   {
        #       'name': 'rm_zero_value_trials',
        #        'config': [{'zeros_to_count': 1}, {'digit_tolerance': 0}]
        #   }
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

        @post
        def filter_moving_average(trial_data, config):
            args = config['config']
            logger = MultiProcessingLog.get_logger()
            window_size = args[0]['window_size']

            # Ensure window size is always odd
            if window_size % 2 == 0:
                window_size += 1
            window_sides = int((window_size - 1)/2)

            data = trial_data['trial']['data']
            new_data = []
            pad_data = list(data[:window_size][::-1]) + list(data) + list(data[-window_size:][::-1])
            for count, _ in enumerate(pad_data):
                if count <= window_size - 1 or count > (len(pad_data) - 1) - window_size:
                    continue

                window = pad_data[count-window_sides:count] +\
                         [pad_data[count]] +\
                         pad_data[count+1:count+window_sides+1]

                avg = np.mean(window)
                new_data.append(avg.copy())

            trial_data['trial']['data'] = new_data
            return trial_data

        @post
        def filter_fft(trial_data, config):
            args = config['config']
            logger = MultiProcessingLog.get_logger()

            high_freq = args[0]['highest_freq']
            low_freq = args[1]['lowest_freq']
            srate = trial_data['srate']

            data = trial_data['trial']['data']
            if 'trial_proc' in data:
                data = trial_data['trial_proc']['data']
            else:
                trial_data['trial_proc'] = {
                    'data': [],
                    'timestamps': trial_data['trial']['timestamps']
                }

            trial_data['trial_proc']['data'] = filter_fft_data(data, low_freq, high_freq, srate)
            return trial_data

        self.pre_processing = pre
        self.post_processing = post