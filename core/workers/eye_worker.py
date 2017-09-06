from core.utilities.MPLogger import MultiProcessingLog
from core.workers.trigger_worker import PLibTriggerWorker
from core.workers.processors.eye_processor import EyeProcessor
import core.utilities.utilities as utilities
from threading import Thread
import os
import threading
import copy


class PLibEyeWorker(Thread):
    def __init__(self, config, eye_dataset=None, markers=None):
        Thread.__init__(self)
        self.config = copy.deepcopy(config)    # Metadata about how to process the given datasets.
        self.eye_dataset = eye_dataset
        self.config['srate'] = eye_dataset['srate']
        self.markers = markers
        self.logger = MultiProcessingLog.get_logger()

        self.initial_data = {
            'config': config,    # Metadata about how to process the given datasets.
            'eye_dataset': eye_dataset,
            'markers': markers
        }

        self.trigger_data = {}
        self.proc_data = {}

    def run(self):
        self.trigger_data = {}
        self.proc_data = {}

        print('self.config[triggers]: ' + str(self.config['triggers']))
        if self.config['testing']:
            self.logger.send('INFO', 'I am an eye worker. I split the triggers.', os.getpid(), threading.get_ident())

        # If this eye is in the yaml config, specify it's
        # configuration by replacing the current one with a new one.
        self.config = utilities.parse_yaml_for_config(self.config, self.getName())
        print(self.getName())

        # Run the pre processors.
        eye_processor = None
        if self.config['eye_pre_processing']:
            eye_processor = EyeProcessor()

            for config in self.config['eye_pre_processing']:
                if config['name'] in eye_processor.pre_processing.all:
                    eye_processor.pre_processing.all[config['name']](self.initial_data, config)

        trigger_workers = {}
        base_trig_worker = PLibTriggerWorker(self.config, self.eye_dataset)
        parallel = False
        # For each trigger, get the number of trials that are within
        # each of them and start a thread to process those.
        for i in self.config['triggers']:
            inds = utilities.get_marker_indices(self.markers['eventnames'], i)
            proc_mtimes = utilities.indVal(self.markers['timestamps'], inds)
            if len(proc_mtimes) == 0:
                self.logger.send('WARNING', 'The trigger name ' + i + ' cannot be found in the dataset.', os.getpid(),
                            threading.get_ident())
                continue

            self.trigger_data[i] = {}
            # If we have enough workers available, do them all in parallel.
            # Otherwise, we simply do them sequentially.
            if self.config['max_workers'] > self.config['num_datasets'] + \
                    self.config['num_eyes'] + self.config['total_triggers']:
                trigger_worker = PLibTriggerWorker(self.config, self.eye_dataset, inds, proc_mtimes, copy.deepcopy(i))
                trigger_worker.setName(self.getName() + ":trigger" + i)
                trigger_workers[i] = trigger_worker
                trigger_worker.start()
                parallel = True
            else:
                base_trig_worker.setName(self.getName() + ":trigger" + i)
                base_trig_worker.marker_inds = inds
                base_trig_worker.marker_times = proc_mtimes
                base_trig_worker.marker_name = copy.deepcopy(i)
                base_trig_worker.reset_initial_data()
                base_trig_worker.run()
                self.trigger_data[i] = copy.deepcopy(base_trig_worker.proc_trigger_data)

        if parallel:
            for i in trigger_workers:
                trigger_workers[i].join()
            #self.logger.send('INFO', 'Done all eyes for ' + self.getName())
            for i in self.config['triggers']:
                self.trigger_data[i] = copy.deepcopy(trigger_workers[i].proc_trigger_data)

        self.proc_data = {
            'config': {
                'eye_dataset': self.eye_dataset,
                'name': self.getName()
            },
            'triggers': self.trigger_data,
        }

        # Run the post processors.
        if self.config['eye_post_processing']:
            if not eye_processor:
                eye_processor = EyeProcessor()

            for config in self.config['eye_post_processing']:
                if config['name'] in eye_processor.post_processing.all:
                    eye_processor.post_processing.all[config['name']](self.proc_eye_data, config)
