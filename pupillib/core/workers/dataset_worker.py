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
import threading
from threading import Thread

from pupillib.core.utilities.MPLogger import MultiProcessingLog
from pupillib.core.workers.eye_worker import PLibEyeWorker
from pupillib.core.workers.generic_eye_level_worker import GenericEyeLevelWorker
from pupillib.core.workers.processors.dataset_processor import DatasetProcessor

from pupillib.core.utilities import utilities


class PLibDatasetWorker(Thread):
    def __init__(self, config, dataset=None):
        Thread.__init__(self)
        self.config = config    # Metadata about how to process the given datasets.
        self.dataset = dataset
        self.logger = MultiProcessingLog.get_logger()

        self.initial_data = {
            'config': config,    # Metadata about how to process the given datasets.
            'dataset': dataset,
        }

        self.proc_eye_data = {}
        self.proc_generic_data = {}
        self.proc_dataset_data = {}

    def run_eye_workers(self):
        # If this dataset is in the yaml config, specify it's
        # configuration by replacing the current one with a new one.
        self.config = utilities.parse_yaml_for_config(self.config, self.getName())

        # Run the pre processors.
        # Run the pre processors.
        dataset_processor = DatasetProcessor()
        self.initial_data['dataset'] = self.dataset
        rejected_streams = dataset_processor.reject_streams(self.initial_data)
        self.initial_data['dataset'] = {
            name: data
                for name, data in self.initial_data['dataset'].items()
                if name not in rejected_streams
        }
        if len(rejected_streams) > 0:
            self.logger.send(
                'INFO', 'Rejecting the following streams: ' + str(rejected_streams), os.getpid(), threading.get_ident()
            )
            if 'all' in rejected_streams:
                self.logger.send(
                    "INFO", "No data was given, or all streams are broken.", os.getpid(), threading.get_ident()
                )
                return None

        if self.config['dataset_pre_processing']:
            for config in self.config['dataset_pre_processing']:
                if config['name'] in dataset_processor.pre_processing.all:
                    self.initial_data = dataset_processor.pre_processing.all[config['name']](self.initial_data, config)
        self.dataset = self.initial_data['dataset']

        eye_worker0 = PLibEyeWorker(self.config, self.dataset['eye0'], self.dataset['markers'])
        eye_worker1 = PLibEyeWorker(self.config, self.dataset['eye1'], self.dataset['markers'])
        eye_workers = [eye_worker0, eye_worker1]
        if self.config['max_workers'] >= self.config['num_datasets'] + self.config['num_eyes']:
            eye_count = 0
            for i in eye_workers:
                i.setName(self.getName() + ':eye' + str(eye_count))
                eye_count += 1
                i.start()
            for i in eye_workers:
                i.join()
        else:
            if 'eye0' not in rejected_streams:
                eye_worker0.setName(self.getName() + ':eye0')
                eye_worker0.run()
            if 'eye1' not in rejected_streams:
                eye_worker1.setName(self.getName() + ':eye1')
                eye_worker1.run()

        eye_count = 0
        self.proc_dataset_data = {
            'config': {
                'name': self.getName(),
                'srate': eye_worker0.proc_data['config']['srate']
            },
            'data': {
                'eye0': eye_worker0.proc_data,
                'eye1': eye_worker1.proc_data
            }
        }

        # Run the post processors.
        if self.config['dataset_post_processing']:
            if not dataset_processor:
                dataset_processor = DatasetProcessor()

            for config in self.config['dataset_post_processing']:
                if config['name'] in dataset_processor.post_processing.all:
                    dataset_processor.post_processing.all[config['name']](self.proc_dataset_data, config)

    def run_generic_workers(self):
        # If this dataset is in the yaml config, specify it's
        # configuration by replacing the current one with a new one.
        testing = self.config['testing']
        self.config = utilities.parse_yaml_for_config(self.config, self.getName())

        # Run the pre processors.
        dataset_processor = DatasetProcessor()
        self.initial_data['dataset'] = self.dataset
        rejected_streams = dataset_processor.reject_streams(self.initial_data)
        self.initial_data['dataset'] = {
            name: data
            for name, data in self.initial_data['dataset'].items()
            if name not in rejected_streams
        }
        if len(rejected_streams) > 0:
            self.logger.send(
                'INFO', 'Rejecting the following streams: ' + str(rejected_streams), os.getpid(), threading.get_ident()
            )
            if 'all' in rejected_streams:
                self.logger.send(
                    "INFO", "No data was given, or all streams are broken.", os.getpid(), threading.get_ident()
                )
                return None
        self.dataset = self.initial_data['dataset']

        if self.config['dataset_pre_processing']:
            for config in self.config['dataset_pre_processing']:
                if config['name'] in dataset_processor.pre_processing.all:
                    self.initial_data = dataset_processor.pre_processing.all[config['name']](self.initial_data, config)
            self.dataset = self.initial_data['dataset']

        generic_workers = {}
        base_generic_worker = GenericEyeLevelWorker(self.config)
        proc_data_for_data_name = {}
        parallel = False

        srate = 0
        datanames = self.dataset['dataname_list']
        for data_name in datanames:
            if data_name in rejected_streams:
                continue
            data_for_data_name = self.dataset[data_name]

            if self.config['max_workers'] >= self.config['num_datasets'] + len(datanames):
                generic_worker = GenericEyeLevelWorker(self.config, data_for_data_name, self.dataset['markers'])
                generic_worker.setName(self.getName() + ":" + data_name)
                generic_workers[data_name] = generic_worker
                generic_worker.start()
                parallel = True
            else:
                base_generic_worker.setName(self.getName() + ":" + data_name)
                base_generic_worker.set_data(data_for_data_name, self.dataset['markers'])
                base_generic_worker.run()
                proc_data_for_data_name[data_name] = base_generic_worker.proc_data
                base_generic_worker.reset_initial_data()

        if parallel:
            for data_name in generic_workers:
                generic_workers[data_name].join()
            for data_name in datanames:
                proc_data_for_data_name[data_name] = generic_workers[data_name].proc_data

        self.proc_dataset_data = {
            'config': {
                'name': self.getName(),
                'srate': base_generic_worker.proc_data['config']['srate']
            }
        }

        self.proc_generic_data = proc_data_for_data_name
        self.proc_dataset_data['data'] = proc_data_for_data_name

        # Run the post processors.
        if self.config['dataset_post_processing']:
            if not dataset_processor:
                dataset_processor = DatasetProcessor()

            for config in self.config['dataset_post_processing']:
                if config['name'] in dataset_processor.post_processing.all:
                    dataset_processor.post_processing.all[config['name']](self.proc_dataset_data, config)

    def run(self):
        if self.config['testing']:
            self.logger.send('INFO', 'Dataset worker is here.', os.getpid(), threading.get_ident())
        if self.dataset is None:
            self.logger.send('ERROR', 'Dataset worker is missing a dataset', os.getpid(), threading.get_ident())
            return

        # TODO: Completely disable and remove eye_workers if possible
        if not self.dataset['custom_data']:
            self.run_eye_workers()
        else:
            self.logger.send('INFO', 'Processing custom data.')
            self.run_generic_workers()
        self.logger.send('INFO', 'Done all data streams for ' + self.getName())
