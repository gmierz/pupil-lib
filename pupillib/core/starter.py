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

print(os.getcwd())
os.system("py core/pupil_lib.py --datasets C:\\Users\\Gregory\\Documents\\Honors_Thesis\\2017_03_07\\002 "
          "C:\\Users\\Gregory\\Documents\\Honors_Thesis\\2017_03_07\\002 --triggers S11 S12 S13 "
          "--trial-range -1 2 --baseline 1 --store artifacts/2017_06_24/ --logger stdout --max-workers 17")