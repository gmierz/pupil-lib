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

DSTREAMS_BLACKLIST = [
    'name',
    'markers',
    'dir',
    'custom_data',
    'merged',
    'dataname_list',
    'dataset_name'
]

class DatasetDefaults():
    @staticmethod
    def pre_defaults():
        return [{'name': 'custom_resample_stream', 'config': [{'srate': 256}]}]

    @staticmethod
    def post_defaults():
        return []


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

        def pick_best_stream(dataset_data):
            all_data = {
                dset: dataset_data['dataset'][dset]
                for dset in dataset_data['dataset']
                if dset not in DSTREAMS_BLACKLIST
            }

            data_mins = {}
            data_maxs = {}
            for dataname in all_data:
                data_mins[dataname] = all_data[dataname]['timestamps'][0]
                data_maxs[dataname] = all_data[dataname]['timestamps'][-1]

            abs_min = 0
            abs_max = 0
            min_dataname = ''
            max_dataname = ''
            done = 0
            for dataname in data_mins:
                if done == 0:
                    abs_min = data_mins[dataname]
                    abs_max = data_maxs[dataname]
                    min_dataname = dataname
                    max_dataname = dataname
                    done += 1
                    continue
                if data_mins[dataname] > abs_min:
                    abs_min = data_mins[dataname]
                    min_dataname = dataname
                if data_maxs[dataname] < abs_max:
                    abs_max = data_maxs[dataname]
                    max_dataname = dataname
            return min_dataname, max_dataname

        @pre
        def custom_resample_stream(dataset_data, config):
            print('Resampling data streams to regular sampling rates...')
            args = config['config']
            logger = MultiProcessingLog.get_logger()

            # Get srate
            srate = args[0]['srate']
            if len(dataset_data['dataset']) <= 1:
                return dataset_data

            min_dataname, max_dataname = pick_best_stream(dataset_data)
            min_datastream = dataset_data['dataset'][min_dataname]['timestamps']
            max_datastream = dataset_data['dataset'][max_dataname]['timestamps']
            global_min = min_datastream[0]
            global_max = max_datastream[-1]

            all_data = {
                dataname: dataset_data['dataset'][dataname]
                    for dataname in dataset_data['dataset']
                    if dataname not in DSTREAMS_BLACKLIST
            }
            for dataname in all_data:
                dstream = all_data[dataname]
                data_ts = dstream['timestamps']
                data_dset = dstream['data']

                # Replace start points
                cur_start = 0
                cur_min = data_ts[0]
                new_data_ts = data_ts
                new_data_dset = data_dset
                if cur_min != global_min:
                    new_data_ts = []
                    for count, _ in enumerate(data_ts[:-1]):
                        if data_ts[count] < global_min <= data_ts[count+1]:
                            cur_start = count
                            break

                    # Replace first data points
                    new_data_ts = data_ts[cur_start:]
                    new_data_dset = data_dset[cur_start:]

                    # Interpolate a new data point
                    new_data_dset[0] = linear_approx(
                        new_data_dset[0], new_data_ts[0],
                        new_data_dset[1], new_data_ts[1],
                        global_min
                    )
                    new_data_ts[0] = global_min

                # Replace end points
                cur_max = data_ts[-1]
                if cur_max != global_max:
                    cur_end = len(data_ts) - 1
                    cur_end_offset = 0
                    reved_ts = data_ts[::-1]
                    for count, _ in enumerate(reved_ts):
                        if reved_ts[count] >= global_max > reved_ts[count+1]:
                            cur_end_offset = count
                            break

                    # Second value of slice is exclusive, add 1
                    # to keep the value (it's going to be replaced)
                    cur_end = cur_end - cur_end_offset + 1
                    new_data_ts = new_data_ts[:cur_end]
                    new_data_dset = new_data_dset[:cur_end]

                    # Interpolate a new data point
                    new_data_dset[-1] = linear_approx(
                        new_data_dset[-2], new_data_ts[-2],
                        new_data_dset[-1], new_data_ts[-1],
                        global_max
                    )
                    new_data_ts[-1] = global_max

                new_dstream = dstream
                if srate != 'None' and srate is not None:
                    print('Resampling trials to ' + str(srate) + 'Hz...')
                    total_time = global_max - global_min
                    new_xrange = np.linspace(global_min, global_max, num=srate * (total_time))

                    new_dstream['data'] = np.interp(new_xrange, new_data_ts, new_data_dset)
                    new_dstream['timestamps'] = new_xrange

                    dataset_data['dataset'][dataname] = new_dstream

            for dset in dataset_data['dataset']:
                if dset in DSTREAMS_BLACKLIST:
                    continue
                print(
                    "Len for " + dset + ": " + str(len(dataset_data['dataset'][dset]['data']))
                )
            return dataset_data

        self.pre_processing = pre
        self.post_processing = post
        self.rejected_streams = []


    def reject_streams(self, dataset_data):
        all_data = {
            dset: dataset_data['dataset'][dset]
                for dset in dataset_data['dataset']
                if dset not in DSTREAMS_BLACKLIST
        }

        if not all_data or len(all_data.keys()) <= 0:
            self.rejected_streams.append('all')
            return ['all']

        for dataname in all_data:
            try:
                data = all_data[dataname]['timestamps']
                min_data = data[0]
                max_data = data[-1]
                if min_data == max_data:
                    print("ERROR: Datastream " + dataname + "has only one value in it, skipping it.")
                    self.rejected_streams.append(dataname)
            except Exception as e:
                self.rejected_streams.append(dataname)
        return self.rejected_streams