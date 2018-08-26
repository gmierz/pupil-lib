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
from frozendict import frozendict


class ConfigStore:

    class innerConfigStore:
        def __init__(self, config):
            self.frozen_config = frozendict(config)

    instance = None

    @staticmethod
    def get_instance(a_dict=None):
        if a_dict is None:
            a_dict = dict()
        if not ConfigStore.instance:
            ConfigStore.instance = ConfigStore.innerConfigStore(a_dict)
        else:
            return ConfigStore.instance

    @staticmethod
    def set_instance(a_dict=None):
        if a_dict is None:
            a_dict = dict()
        if not ConfigStore.instance:
            ConfigStore.instance = ConfigStore.innerConfigStore(a_dict)