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

import pytest

# Basic extraction tests - these tests are testing the overall pipeline
from pupillib.pupil_lib import script_run

OLD_PUPIL_LSL = 'resources/test_yaml1.yml'
NEW_PUPIL_LSL = 'resources/test_yaml3.yml'

def test_pupil_lsl1():
    # Test that extraction works correctly with old LSL
    # relay data.
    import os
    print(os.getcwd())
    if not os.path.exists(OLD_PUPIL_LSL):
        assert False
    plibrunner = script_run(yaml_path=OLD_PUPIL_LSL, quiet=True)

    # Make sure data, and datastore exist
    assert plibrunner.data_store
    assert plibrunner.data

