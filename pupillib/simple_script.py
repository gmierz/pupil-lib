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
import json
import numpy as np
from matplotlib import pyplot as plt

from pupillib.core.workers.processors.trial_processor import (
    filter_fft_data,
    filter_rm_trials_with_vals_gt,
    filter_rm_trials_with_vals_lt
)
from pupillib.pupil_lib import script_run

def main():
    # Load the datasets and run, if `cache` is specified, the data will be saved after processing
    # and used in subsequent runs. Change the path, or remove the flag to prevent caching.
    plibrunner = script_run(yaml_path='resources/test_yaml1.yml', cache='resources/saved_data1.json')

    # After this the plibrunner will hold information about the datasets,
    # and it can be stored for viewing, and extra processing later.
    datastore = plibrunner.data_store
    print('Last stage')

    datastore.time_or_data = 'data'
    trigs = ['S11', 'S12', 'S13', 'S14']
    col = {'S11': 'blue', 'S12': 'r', 'S13': 'g', 'S14': 'black'}
    datastore.data_type = 'pc'

    '''
    # Examples using the processor functions

    # Band-pass filter with fft to keep frequencies in the range [0, 20]
    datastore.process_trials(filter_fft_data, low_freq=0, high_freq=20, srate=256)

    # Set to 'proc' to use data processed by FFT
    #datastore.data_type = 'proc'

    # Remove trials with values greater than 0.2, and less than -0.5
    datastore.process_trials(filter_rm_trials_with_vals_gt, gtval=0.2)
    datastore.process_trials(filter_rm_trials_with_vals_lt, ltval=-0.5)
    '''

    dat_mat = datastore.datasets['dataset1'].data_streams['gaze_x'].triggers['S11'].get_matrix()
    plt.figure()
    for i in dat_mat:
        plt.subplot(2, 1, 1)
        plt.plot(np.linspace(0, 4000, num=len(i)), i)
        plt.xlabel('Time (milli-seconds)')
        plt.ylabel('X Eye Movement (gaze x)')
    plt.axhline(0, color='r')
    plt.axvline(1000, color='r')
    plt.axvline(3000, color='r')

    dat_mat = datastore.datasets['dataset1'].data_streams['gaze_y'].triggers['S11'].get_matrix()
    plt.subplot(2, 1, 2)
    for i in dat_mat:
        plt.plot(np.linspace(0, 4000, num=len(i)), i)
        plt.xlabel('Time (milli-seconds)')
        plt.ylabel('Y Eye Movement (gaze y)')
    plt.axhline(0, color='r')
    plt.axvline(1000, color='r')
    plt.axvline(3000, color='r')

    datastore.data_type = 'pc'

    plt.figure()
    for i in range(len(trigs)):
        plt.subplot(2, 2, i + 1)
        dat_mat = datastore.datasets['dataset2'].data_streams['eye0'].triggers[trigs[i]].get_matrix()
        for trial in dat_mat:
            plt.plot(np.linspace(0, 4000, num=len(trial)), trial)
        plt.title('Trigger: ' + trigs[i])
        if i >= 2:
            plt.xlabel('Time (milli-seconds)')
        plt.ylabel('Percent Change Diameter')
        plt.axhline(0, color='r')
        plt.axvline(1000, color='r')
        plt.axvline(3000, color='r')

    plt.figure()
    for trig in trigs:
        line_y = np.mean(datastore.datasets['dataset2'].data_streams['eye0'].triggers[trig].get_matrix(), 0)
        plt.plot(np.linspace(0, 4000, num=len(line_y)), line_y,
                 col[trig], label=trig)
    plt.legend()
    plt.xlabel('Time (milli-seconds)')
    plt.ylabel('Percent Change Diameter')
    plt.axhline(0, color='r')
    plt.axvline(1000, color='r')
    plt.axvline(3000, color='r')

    plt.show(block=True)

    # datastore.save_csv('C:/Users/Gregory/PycharmProjects/pupil_lib_parallel_exp/', name=str(int(time.time())))


if __name__ == "__main__":
    main()