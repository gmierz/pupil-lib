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
from setuptools import setup

setup(
    name = "pupillib",
    version = "1.2.1",
    author = "Gregory Mierzwinski",
    author_email = "gmierz1@live.ca",
    description = ("A software package to perform trial extraction on Pupil Labs eye "
                   "tracker data collected into XDF files through LabRecorder."),
    license = "GPLv3",
    keywords = "trial extraction pupil labs",
    url = "https://github.com/gmierz/pupil-lib-python/",
    packages=[
        'pupillib',
        'pupillib.core',
        'pupillib.core.utilities',
        'pupillib.core.workers',
        'pupillib.core.workers.processors',
        'pupillib.core.workers.processors.processing_functions',
        'pupillib.dependencies',
        'pupillib.dependencies.xdf',
        'pupillib.dependencies.xdf.Python',
    ],
    long_description="See this page: https://github.com/gmierz/pupil-lib-python/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering",
    ],
    install_requires=[
        'msgpack',
        'frozendict',
        'cycler',
        'matplotlib',
        'numpy',
        'pip',
        'pyparsing',
        'python-dateutil',
        'pytz',
        'ruamel.yaml',
        'six'
    ],
    entry_points="""
    # -*- Entry points: -*-
    [console_scripts]
    pupillib = pupillib.pupil_lib:main
    """,
)