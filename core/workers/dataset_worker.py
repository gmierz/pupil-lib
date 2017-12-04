from core.utilities.MPLogger import MultiProcessingLog
from core.workers.eye_worker import PLibEyeWorker
from core.workers.generic_eye_level_worker import GenericEyeLevelWorker
from core.workers.processors.dataset_processor import DatasetProcessor
from core.utilities import utilities
from threading import Thread
import os
import threading


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
        dataset_processor = None
        if self.config['dataset_pre_processing']:
            dataset_processor = DatasetProcessor()

            for config in self.config['dataset_pre_processing']:
                if config['name'] in dataset_processor.pre_processing.all:
                    dataset_processor.pre_processing.all[config['name']](self.initial_data, config)


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
            eye_worker0.setName(self.getName() + ':eye0')
            eye_worker0.run()

            eye_worker1.setName(self.getName() + ':eye1')
            eye_worker1.run()

        eye_count = 0
        self.proc_dataset_data = {
            'config': {
                'name': self.getName(),
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
        print(self.config)
        self.config = utilities.parse_yaml_for_config(self.config, self.getName())

        # Run the pre processors.
        dataset_processor = None
        if self.config['dataset_pre_processing']:
            dataset_processor = DatasetProcessor()

            for config in self.config['dataset_pre_processing']:
                if config['name'] in dataset_processor.pre_processing.all:
                    dataset_processor.pre_processing.all[config['name']](self.initial_data, config)

        self.proc_dataset_data = {
            'config': {
                'name': self.getName()
            }
        }

        generic_workers = {}
        base_generic_worker = GenericEyeLevelWorker(self.config)
        proc_data_for_data_name = {}
        parallel = False

        datanames = self.dataset['dataname_list']
        for data_name in datanames:
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

        if parallel:
            for data_name in generic_workers:
                generic_workers[data_name].join()
            for data_name in datanames:
                proc_data_for_data_name[data_name] = generic_workers[data_name].proc_data

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
        if not self.dataset['custom_data']:
            self.run_eye_workers()
        else:
            self.logger.send('INFO', 'Processing custom data.')
            self.run_generic_workers()
        self.logger.send('INFO', 'Done all eyes for ' + self.getName())
