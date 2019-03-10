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

def main():
    # Load the datasets and run
    plibrunner = script_run(
        yaml_path='pupillib/resources/test_yaml_xdf_to_csv.yml'
    )

    # After this the plibrunner will hold information about the datasets,
    # and it can be stored for viewing, and extra processing later.
    datastore = plibrunner.data_store
    len0 = len(datastore.datasets['dataset1'].data_streams['eye0'].data)
    len1 = len(datastore.datasets['dataset1'].data_streams['eye1'].data)
    print('length of eye0 datastream: ' + str(len0))
    print('length of eye1 datastream: ' + str(len1))

    datastore.save_rawstream_csv(
        output_dir='', name='testing_rawstream' + str(int(time.time()))
    )
    print("Sampling rate: {}".format(datastore.srate))
    print("Done saving.")

if __name__ == "__main__":
    main()