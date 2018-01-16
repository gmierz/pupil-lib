import numpy as np
import sys
import math
import copy
import codecs

# GET_ERROR Retrieves an error of the distance between two values and the
# input time.
#   INPUT:
#       val1 - First value to use.
#       val2 - Second value to use.
#       time - Value to check against.
#
def get_error(value1, value2, time):
    return (value1 - value2) - time


# LINEAR_APPROX Used to approximate a diameter at an intermediate point.
#   This will take two diameters and two timestamps, along with a time and
#   it will output a linear approximation for that time
#
#   diameter
#       ^
#       |       x
#       |      / (ts2, val2)
# val_out|____/
#       |    /|
#       |   / |
#       |  x  |
#       |   (ts1, val1)
#       |-----|------------------> timestamps
#             |
#          ts_final
#
#
#   INPUT: Described through the graph.
#
def linear_approx(val1, ts1, val2, ts2, ts_final, error=None, default_val=0):
    if error is not None:
        if error == 0:
            return val1 if default_val == 1 else val2
    line_slope = (val2 - val1) / (ts2 - ts1)
    line_const = (val1 - (ts1 * line_slope))
    return (ts_final * line_slope) + line_const


# MAKE_EPOCHMAT Produces a matrix of epochs in a given pupil dataset.
def make_epochmat(PUPIL_EPOCHED, trigger_ind):
    # Produce a matrix of the epoch data across all epochs.
    print('before mat:')
    len_dat = np.size(PUPIL_EPOCHED.eye0.epochs[0]['epochs'][0]['data'])
    print(PUPIL_EPOCHED.eye0.epochs[0]['epochs'][0]['data'][1:len_dat])
    epoch_size = np.size(PUPIL_EPOCHED.eye0.epochs[trigger_ind]['epochs'])
    print('epochs')
    print(epoch_size)
    data_size = np.size(PUPIL_EPOCHED.eye0.epochs[trigger_ind]['epochs'][0]['data'])
    PUPIL_EPOCHED.eye0.epochs[trigger_ind]['epochmat'] = \
        np.zeros((epoch_size, data_size))
    for l in range(0, epoch_size, 1):
        PUPIL_EPOCHED.eye0.epochs[trigger_ind]['epochmat'][l, :] = \
            PUPIL_EPOCHED.eye0.epochs[trigger_ind]['epochs'][l]['data']

    epoch_size = np.size(PUPIL_EPOCHED.eye1.epochs[trigger_ind]['epochs'])
    data_size = np.size(PUPIL_EPOCHED.eye1.epochs[trigger_ind]['epochs'][0]['data'])
    PUPIL_EPOCHED.eye1.epochs[trigger_ind]['epochmat'] = \
        np.zeros((epoch_size, data_size))
    for l in range(0, epoch_size, 1):
        PUPIL_EPOCHED.eye1.epochs[trigger_ind]['epochmat'][l, :] = \
            PUPIL_EPOCHED.eye1.epochs[trigger_ind]['epochs'][l]['data']

    print('after mat:')
    print(PUPIL_EPOCHED.eye0.epochs[trigger_ind]['epochmat'][0,:])

    return PUPIL_EPOCHED


# MAKE_RMB_PC_MATS Used to produce the percent change graph and remove the
# baseline from a measurement.
def make_rmb_pc_mats(PUPIL_EPOCHED, trig_ind):
    # Remove the baseline and get the rest mean for each set of
    # trigger.

    k = trig_ind

    # Get baseline removed data set.
    [PUPIL_EPOCHED.eye0.epochs[k]['epochmat_rmb'], PUPIL_EPOCHED.eye0.epochs[k]['rest_mean']] = \
        PUPIL_EPOCHED.eye0.pupil_rmbaselineeye(0, k)

    [PUPIL_EPOCHED.eye1.epochs[k]['epochmat_rmb'], PUPIL_EPOCHED.eye1.epochs[k]['rest_mean']] = \
        PUPIL_EPOCHED.eye1.pupil_rmbaselineeye(0, k)

    # Calculate the percent change graph.
    PUPIL_EPOCHED.eye0.epochs[k]['epochmat_pc'] = PUPIL_EPOCHED.eye0.pupil_datapercenteye(k)
    PUPIL_EPOCHED.eye1.epochs[k]['epochmat_pc'] = PUPIL_EPOCHED.eye1.pupil_datapercenteye(k)
    return PUPIL_EPOCHED


# PARSE_TRIGS Parses a pupil entry for a trigger index.
#   INPUT:
#       PUPIL - PUPIL data, which has the same epoch triggers in each eye.
#       trig  - The name of the trigger in the form of a string.
#
def parse_trigs(PUPIL_EYE, trig):
    for i in range(0, np.size(PUPIL_EYE.epochs, 2)-1, 1):
        if trig == PUPIL_EYE.epochs[i].name:
            return i


'''
    Both of these are used to handle errors that are recognized
    in the pupil analyzer. *args lets you set a status code.
'''
def error(msg, *args):
    status_code = 1
    for arg in args:
        status_code = arg
    np.disp('Error found: ' + msg)
    sys.exit(status_code)


'''
    Can be used to obtain indices using a lambda function.
'''
def indices(a, func):
    return [i for (i, val) in enumerate(a) if func(val)]

'''
    Can be used to obtain values at a given set of indices.
'''
def indVal(list_used, indices):
    return [list_used[i] for i in indices]

'''
    Filter out 'nan' numbers from a list, and it's associated list.
'''
def nanFilter(data, ts):
    inds = []
    for i in range(0, len(data), 1):
        if math.isnan(data[i]):
            inds.append(i)
    full_ind0 = range(0, len(data), 1)
    inds0 = [i for i in full_ind0 if i not in inds]

    for i in range(0, len(inds0), 1):
        if inds0[i] in inds:
            print('failure')

    return [indVal(data, inds0), indVal(ts, inds0)]

'''
    Gets the indicies for a given marker name from a set of marker
    names corresponding to an entire pupil experiment.
'''
def get_marker_indices(marker_names, trig):
    inds = []
    for i in range(0, np.size(marker_names)):
        if marker_names[i] == trig:
            inds.append(i)
    return inds


def custom_interval_upsample(data, times, interval):
    new_data = []
    new_times = []
    old_length = len(data)
    final_ind = old_length - 1
    beforeLast_ind = final_ind - 1

    for i in range(0, beforeLast_ind):
        new_data.append(data[i])
        new_times.append(times[i])

        curr_time = times[i]
        next_time = times[i + 1]
        while curr_time + interval < next_time:
            curr_time = curr_time + interval
            new_times.append(curr_time)
            new_data.append(
                linear_approx(data[i], times[i], data[i + 1], times[i + 1], curr_time))

        if i == beforeLast_ind-1:
            new_data.append(data[i+1])
            new_times.append(times[i+1])

    return [new_data, new_times]

# Don't replace these fields.
BLACKLIST = {
    'parsed_yaml': False,
    'max_workers': False,
    'logger': False,
    'store': False
}
def parse_yaml_for_config(config, name):
    if name not in config['parsed_yaml']:
        return config

    new_config = copy.deepcopy(config)
    name_config = config['parsed_yaml'][name]

    for option in name_config:
        if option not in BLACKLIST:
            new_config[option] = name_config[option]
    return new_config


def jsonify_pd(data):
    new_data = data
    if isinstance(data, dict):
        for name, val in data.items():
            new_data[name] = jsonify_pd(val)
    elif isinstance(data, np.ndarray):
        new_data = data.tolist()
    elif isinstance(data, set):
        new_data = list(data)
    return new_data


def union(a, b):
    return list(set(a) | set(b))