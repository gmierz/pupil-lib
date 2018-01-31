from setuptools import setup

setup(
    name = "pupillib",
    version = "0.0.0",
    author = "Gregory Mierzwinski",
    author_email = "gmierz1@live.ca",
    description = ("A software package to perform trial extraction on Pupil Labs eye "
                   "tracker data collected into XDF files through LabRecorder."),
    license = "GPLv2",
    keywords = "trial extraction pupil labs",
    url = "https://github.com/gmierz/pupil-lib-python/",
    packages=['pupillib'],
    long_description="See this page: https://github.com/gmierz/pupil-lib-python/",
    classifiers=[
        "Development Status :: Beta",
    ],
    install_requires=[
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
)