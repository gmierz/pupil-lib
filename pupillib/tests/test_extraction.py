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

import os
import sys
import pytest

# Basic extraction tests - these tests are testing the overall pipeline
from pupillib.pupil_lib import script_run

OLD_PUPIL_LSL = 'resources/test_yaml1.yml'
NEW_PUPIL_LSL = 'resources/test_yaml3.yml'

class StdOutDisabled(object):
    # Disables all prints in pupillib
    def __enter__(self):
        sys.stdout = None
    def __exit__(self, type, value, traceback):
        sys.stdout = sys.__stdout__

def test_pupil_lsl1():
    # Test that extraction works correctly with old LSL
    # relay data.
    if not os.path.exists(OLD_PUPIL_LSL):
        assert False

    with StdOutDisabled():
        plibrunner = script_run(yaml_path=OLD_PUPIL_LSL, quiet=True)

    # Make sure data, and datastore exist
    assert plibrunner.data_store
    assert plibrunner.data

    data = plibrunner.data

    assert len(data.datasets) == 2
    assert 'dataset1' in data.datasets
    assert 'dataset2' in data.datasets

    # Datasets
    for dname, dataset in data.datasets.items():
        assert dataset.data and dataset.data_streams

        # Datastreams
        for sname, stream in dataset.data.items():
            assert sname in ['eye0', 'eye1', 'gaze_x', 'gaze_y']
            assert stream.data and stream.triggers

            if dname == 'dataset1' and sname == 'eye0':
                # Trigger list is respecified on this stream, make sure
                # that this is true
                assert len(stream.data) == 1
            else:
                # Trigger list comes from global config here
                assert len(stream.data) == 4

            assert len(stream.raw_data) == len(stream.timestamps)

            # Triggers
            for tname, trigger in stream.data.items():
                # Trigger indices should be equal to the number of trials extracted
                assert tname in ['S11', 'S12', 'S13', 'S14']
                assert trigger.data and trigger.trials
                assert len(stream.trigger_indices[tname]) == len(trigger.data)

                print(trigger.trials[0])
                # Trials
                for i, trial in enumerate(trigger.trials):
                    assert trial.data_type == 'original'
                    assert trial.time_or_data == 'data'

                    assert list(trial.data) == list(trial.original_data)

                    trial.time_or_data = 'timestamps'
                    assert list(trial.data) == list(trial.original_data)
                    assert list(trial.data) == list(trial.get_matrix())

                    # Switch to data and check it switched correctly
                    trial.time_or_data = 'data'
                    datmat = trial.get_matrix()
                    assert list(trial.data) == list(datmat)

                    trial.time_or_data = 'timestamps'
                    times = {
                        'original': trial.original_data,
                        'proc': trial.proc_data,
                        'baserem': trial.baserem_data,
                        'pc': trial.pc_data
                    }

                    trial.time_or_data = 'data'
                    datas = {
                        'original': trial.original_data,
                        'proc': trial.proc_data,
                        'baserem': trial.baserem_data,
                        'pc': trial.pc_data
                    }

                    for dtype in times:
                        assert len(times[dtype]) == len(datas[dtype])

                    if sname == 'eye1' or dname == 'dataset2':
                        # FFT processing has been done, so proc should not be == to original
                        assert list(trial.original_data) != list(trial.proc_data)
                    else:
                        # No processing was done so these should be equal
                        assert list(trial.original_data) == list(trial.proc_data)

                    # Now check the trial times
                    total_trial_time = trial.times[-1] + abs(trial.times[0])
                    if dname == 'dataset1':
                        if sname in ('gaze_x', 'gaze_y', 'eye1'):
                            assert total_trial_time == 5
                        else:
                            if i == 0:
                                assert total_trial_time == 6
                            else:
                                assert total_trial_time == 3
                    else:
                        assert total_trial_time == 3.5


