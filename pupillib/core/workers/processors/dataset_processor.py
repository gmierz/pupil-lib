import os
import threading

from pupillib.core.workers.processors.decorator_registrar import *
from pupillib.core.utilities.MPLogger import MultiProcessingLog
from pupillib.core.utilities.utilities import *

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

class DatasetDefaults():
    @staticmethod
    def pre_defaults():
        return []

    @staticmethod
    def post_defaults():
        return [{'name': 'custom_resample_stream', 'config': [{'srate': 256}]}]


# Provided by Pupil Labs:
# https://github.com/pupil-labs/pupil-docs/blob/master/user-docs/data-format.md#synchronization
def correlate_data(data,timestamps):
    '''
    data:  list of data :
        each datum is a dict with at least:
            timestamp: float

    timestamps: timestamps list to correlate  data to

    this takes a data list and a timestamps list and makes a new list
    with the length of the number of timestamps.
    Each slot contains a list that will have 0, 1 or more associated data points.

    Finally we add an index field to the datum with the associated index
    '''
    timestamps = list(timestamps)
    data_by_frame = [[] for i in timestamps]

    frame_idx = 0
    data_index = 0

    data.sort(key=lambda d: d['timestamp'])

    while True:
        try:
            datum = data[data_index]
            # we can take the midpoint between two frames in time: More appropriate for SW timestamps
            ts = ( timestamps[frame_idx]+timestamps[frame_idx+1] ) / 2.
            # or the time of the next frame: More appropriate for Sart Of Exposure Timestamps (HW timestamps).
            # ts = timestamps[frame_idx+1]
        except IndexError:
            # we might loose a data point at the end but we don't care
            break

        if datum['timestamp'] <= ts:
            datum['index'] = frame_idx
            data_by_frame[frame_idx].append(datum)
            data_index +=1
        else:
            frame_idx+=1

    return data_by_frame

class DatasetProcessor():
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

        @post
        def synch_streams(dataset_data, config):
            print('here')

        @post
        def custom_resample_stream(dataset_data, config):
            print('Resampling data streams to regular sampling rates...')

            datastream_data_eye0 = dataset_data['data']['eye0']['config']['dataset']
            datastream_data_eye1 = dataset_data['data']['eye1']['config']['dataset']

            data0 = datastream_data_eye0['data']
            timestamps0 = datastream_data_eye0['timestamps']

            data1 = datastream_data_eye1['data']
            timestamps1 = datastream_data_eye1['timestamps']

            args = config['config']
            logger = MultiProcessingLog.get_logger()

            # Get srate
            srate = args[0]['srate']

            # Find the first point that is straddled by two
            # points in the other stream.
            first_ind = 0
            first_val = 0
            end_ind = 0
            end_val = 0
            eq_first = False
            eq_end = False

            # Setup
            lower_tset = timestamps1
            higher_tset = timestamps0
            higher_dset = data0
            eye0_or_eye1 = 1
            if timestamps0[0] < timestamps1[0]:
                lower_tset = timestamps0
                higher_tset = timestamps1
                higher_dset = data1
                eye0_or_eye1 = 0

            # Now find the first point
            for i in range(len(lower_tset)):
                if higher_tset[0] <= lower_tset[i]:
                    if lower_tset[i] <= higher_tset[1]:
                        first_ind = i
                        first_val = lower_tset[i]
                        break

            new_data_point = linear_approx(higher_dset[0], higher_tset[0],
                                           higher_dset[1], higher_tset[1],
                                           lower_tset[first_ind])
            higher_dset = higher_dset[1:]
            higher_tset = higher_tset[1:]
            higher_dset[0] = new_data_point
            higher_tset[0] = lower_tset[first_ind]

            if eye0_or_eye1 == 1:
                timestamps1 = lower_tset[first_ind:]
                data1 = data1[first_ind:]

                timestamps0 = higher_tset
                data0 = higher_dset
            else:
                timestamps0 = lower_tset[first_ind:]
                data0 = data0[first_ind:]

                timestamps1 = higher_tset
                data1 = higher_dset

            # Setup for end point
            lower_tset = timestamps1
            higher_tset = timestamps0
            eye0_or_eye1 = 1
            if timestamps0[-1] < timestamps1[-1]:
                lower_tset = timestamps0
                higher_tset = timestamps1
                eye0_or_eye1 = 0

            # Now find the end point
            for i in range(len(lower_tset)):
                if higher_tset[-2] <= lower_tset[i]:
                    if lower_tset[i] <= higher_tset[-1]:
                        end_ind = i
                        end_val = lower_tset[i]
                        break

            new_data_point = linear_approx(higher_dset[-2], higher_tset[-2],
                                           higher_dset[-1], higher_tset[-1],
                                           lower_tset[end_ind])
            higher_dset = higher_dset[:-1]
            higher_tset = higher_tset[:-1]
            higher_dset[-1] = new_data_point
            higher_tset[-1] = lower_tset[end_ind]

            if eye0_or_eye1 == 1:
                timestamps1 = lower_tset[:end_ind+1]
                data1 = data1[:end_ind+1]

                timestamps0 = higher_tset
                data0 = higher_dset
            else:
                timestamps0 = lower_tset[:end_ind+1]
                data0 = data0[:end_ind+1]

                timestamps1 = higher_tset
                data1 = higher_dset

            ## At this point, both streams have the same start and end times (not the same number of points).
            ## Now, all we need to do is take each of their times and resample
            ## it to the given interval.

            if srate != 'None' and srate is not None:
                print('Resampling trials to ' + str(srate) + 'Hz...')
                total_time = end_val - first_val
                new_xrange = np.linspace(first_val, end_val, num=srate*(total_time))

                datastream_data_eye0['data'] = np.interp(new_xrange, timestamps0, data0)
                datastream_data_eye1['data'] = np.interp(new_xrange, timestamps1, data1)

                datastream_data_eye0['timestamps'] = new_xrange
                datastream_data_eye1['timestamps'] = new_xrange

                dataset_data['data']['eye0']['config']['dataset'] = datastream_data_eye0
                dataset_data['data']['eye1']['config']['dataset'] = datastream_data_eye1

                for stream_name in dataset_data['data']:
                    if stream_name in ['eye0', 'eye1']:
                        continue

                    dstream = dataset_data['data'][stream_name]['config']['dataset']
                    new_dstream = dstream
                    new_dstream['data'] = np.interp(new_xrange, dstream['timestamps'], dstream['data'])
                    new_dstream['timestamps'] = new_xrange
                    dataset_data['data'][stream_name]['config']['dataset'] = new_dstream

            return dataset_data

        self.pre_processing = pre
        self.post_processing = post