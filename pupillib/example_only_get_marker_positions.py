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
import time

from pupillib.pupil_lib import script_run, save_csv_line

# Requires a 3D dataset with the form: [trials, values]
# Open a figure befor calling this.
# If standard_error is false then standard deviations will be plotted.
def get_std_dev(matrix, standard_error=True):
    std_tmp = []
    for point in range(matrix.shape[1]):
        std_tmp.append(np.std(np.squeeze(matrix[:, point])))
        if standard_error:
            std_tmp[point] = std_tmp[point] / np.sqrt(matrix.shape[1])
    return std_tmp

def main():
    # Load the datasets and run
    plibrunner = script_run(
        yaml_path='resources/test_yaml2.yml'
    )

    # After this the plibrunner will hold information about the datasets,
    # and it can be stored for viewing, and extra processing later.
    datastore = plibrunner.data_store
    len0 = len(datastore.datasets['dataset1'].data_streams['eye0'].data)
    len1 = len(datastore.datasets['dataset1'].data_streams['eye1'].data)
    print('len0: ' + str(len0))
    print('len1: ' + str(len1))
    from matplotlib import pyplot as plt

    datastore.time_or_data = 'data'
    trigs = ['S11', 'S12', 'S13', 'S14']
    trigger_names = {'S11':'White', 'S12':'Red', 'S13':'Green', 'S14':'colored'}
    col = {'S14': 'blue', 'S11': 'darkorange', 'S13': 'g', 'S12': 'r'}
    datastore.data_type = 'pc'
    alpha = 0.3

    for dataname in datastore.datasets['dataset1'].data_streams:
        dstream = datastore.datasets['dataset1'].data_streams[dataname] # Get raw data
        plt.figure()
        plt.plot(dstream.data, color='black')
        for trig in trigs:
            trig_indices = dstream.trigger_indices[trig] # Get marker indices
            for ind in trig_indices:
                plt.axvline(x=ind, color=col[trig])

    plt.show(block=True)

    print('Main Terminating...')

if __name__ == "__main__":
    main()