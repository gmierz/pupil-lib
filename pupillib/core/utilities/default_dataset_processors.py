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

'''
    This file holds processing function for `pupil_lib.py` to use
    when defaulting to another dataset.
'''

def eye_pyrep_to_prim_default(pyrep_stream, all_data_field, all_data):
    return {
        'data': [eval(el[0])['diameter'] for el in pyrep_stream['time_series']],
        'timestamps': all_data[all_data_field]['timestamps'],
        'srate': all_data[all_data_field]['srate']
    }

def gaze_pyrep_to_prim_default(pyrep_stream, all_data_field, all_data):
    return {
        'data': all_data[all_data_field]['data'],
        'timestamps': all_data[all_data_field]['timestamps'],
        'srate': all_data[all_data_field]['srate']
    }

def gaze_prim_to_pyrep_default(pyrep_stream, all_data_field, all_data):
    return gaze_pyrep_to_prim_default(pyrep_stream, all_data_field, all_data)