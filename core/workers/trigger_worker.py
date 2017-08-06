from core.utilities.MPLogger import MultiProcessingLog
from core.workers.trial_worker import PLibTrialWorker
from core.workers.processors.trigger_processor import *
import core.utilities.utilities as utilities
from threading import Thread
import os
import threading
import copy
import math


class PLibTriggerWorker(Thread):
    def __init__(self, config, eye_dataset=None, marker_inds=None, marker_times=None, marker_name=''):
        Thread.__init__(self)
        self.config = config    # Metadata about how to process the given datasets.
        self.eye_dataset = eye_dataset
        self.data = self.eye_dataset['data']
        self.timestamps = self.eye_dataset['timestamps']
        self.marker_inds = marker_inds
        self.marker_times = marker_times
        self.marker_name = marker_name

        self.initial_data = {
            'config': config,    # Metadata about how to process the given datasets.
            'data': self.eye_dataset['data'],
            'timestamps': self.eye_dataset['timestamps'],
            'marker_inds': self.marker_inds,
            'marker_times': self.marker_times,
            'marker_name': self.marker_name
        }

        # To be initialized
        self.proc_trigger_data = {}
        self.proc_trial_data = {}

        self.logger = MultiProcessingLog.get_logger()

    def reset_initial_data(self):
        self.initial_data = {
            'config': self.config,    # Metadata about how to process the given datasets.
            'data': self.eye_dataset['data'],
            'timestamps': self.eye_dataset['timestamps'],
            'marker_inds': self.marker_inds,
            'marker_times': self.marker_times,
            'marker_name': self.marker_name
        }

    def run(self):
        if self.config['testing']:
            self.logger.send('INFO', 'I am a trigger work. I split the triggers indices into trial workers.', os.getpid(), threading.get_ident())

        # If this trigger is in the yaml config, specify it's
        # configuration by repacing the current one with a new one.
        self.config = utilities.parse_yaml_for_config(self.config, self.getName())

        # Run the pre processors.
        trigger_processor = None
        if self.config['trigger_pre_processing']:
            trigger_processor = TriggerProcessor()

            for config in self.config['trigger_pre_processing']:
                if config['name'] in trigger_processor.pre_processing.all:
                    trigger_processor.pre_processing.all[config['name']](self.initial_data, config)

        # For each trial in a given trigger, start a new thread to retrieve it.
        # Do a deep copy here so that we don't have to deal with access conflicts.
        num_marks = 0
        prev_timestamp = self.timestamps[0]
        data_indices = []
        data_times = []
        data_errors = []
        data_curr_prev = [] # 0 for taking curr, 1 for taking prev
        srate = self.config['srate']
        [baseline, trial_time] = self.config['trial_range']
        base_trial_worker = PLibTrialWorker(self.config)
        trial_workers = {}
        parallel = False
        print('len(self.timestamps)' + str(len(self.timestamps)))

        for index in range(1, len(self.timestamps)):
            # Stop once we've found all of the markers in the data
            if num_marks >= len(self.marker_times):
                break

            # For each timestamp
            curr_timestamp = self.timestamps[index]

            # If we found a spot for a marker
            if prev_timestamp < self.marker_times[num_marks] < curr_timestamp:
                chosen_ind = 0
                if curr_timestamp - self.marker_times[num_marks] > self.marker_times[num_marks] - prev_timestamp:
                    # The current index has a lower error so it should be used.
                    chosen_ind = index-1
                    data_indices.append(index-1)
                    data_times.append(prev_timestamp)
                    data_errors.append(self.marker_times[num_marks] - prev_timestamp)
                    data_curr_prev.append(1)
                elif curr_timestamp - self.marker_times[num_marks] <= self.marker_times[num_marks] - prev_timestamp:
                    # They are equal, pick the current over prev for parity
                    # with Matlab implementation. Or it is a smaller error.
                    chosen_ind = index
                    data_indices.append(index)
                    data_times.append(curr_timestamp)
                    data_errors.append(curr_timestamp - self.marker_times[num_marks])
                    data_curr_prev.append(0)

                # Copy a chunk out. Twice the size, just to be safe.
                # srate: (data points)/second
                # TODO:
                # But first, check to see if this trial number needs a different baseline and trial_time
                # to be cut.
                trial_name = self.getName() + ':trial' + str(num_marks+1)
                baseline_trial = baseline
                trial_time_trial = trial_time

                if 'parsed_yaml' in self.config:
                    if trial_name in self.config['parsed_yaml']:
                        trial_conf = self.config['parsed_yaml'][trial_name]
                        if 'baseline_time' in trial_conf:
                            baseline_trial = trial_conf['baseline_time']
                        if 'trial_time' in trial_conf:
                            trial_time_trial = trial_conf['trial_time']

                baseline_points = int(math.ceil(srate * abs(baseline_trial) * 2))
                trial_points = int(math.ceil(srate * abs(trial_time_trial) * 2))

                # Cut out data
                data_chunk = {
                    'data': copy.deepcopy(
                             self.eye_dataset['data'][chosen_ind - baseline_points:chosen_ind + trial_points + 1]),
                    'timestamps': copy.deepcopy(
                             self.eye_dataset['timestamps'][chosen_ind - baseline_points:chosen_ind + trial_points + 1]),
                    'srate': srate,
                    'marker_ind': baseline_points,
                    'actual_marker_ind': chosen_ind,
                    'actual_marker_time': self.eye_dataset['timestamps'][chosen_ind],
                    'marker_time': self.marker_times[num_marks],
                    'error': data_errors[num_marks],
                    'curr_prev': data_curr_prev[num_marks],
                    'baseline_time_sec': baseline,
                    'trial_time_sec': trial_time
                }

                # Process the trial, either in parallel or sequentially.
                if False:
                    # If we have no limit, run all in parallel.
                    parallel = True
                    trial_worker = PLibTrialWorker(self.config, copy.deepcopy(data_chunk))
                    trial_workers[str(index)] = trial_worker
                    trial_worker.setName(self.getName() + ':trial' + str(num_marks+1))
                    trial_worker.trial_num = str(num_marks+1)
                    trial_worker.start()
                else:
                    # Otherwise, they need to be split.
                    # For now, just run them sequentially.
                    base_trial_worker.setName(self.getName() + ':trial' + str(num_marks + 1))
                    base_trial_worker.chunk_data = data_chunk
                    base_trial_worker.reset_initial_data()
                    base_trial_worker.run()
                    self.proc_trial_data[str(num_marks+1)] = base_trial_worker.proc_trial_data

                # Look for the next marker
                num_marks += 1

            prev_timestamp = curr_timestamp

        if parallel:
            for i in trial_workers:
                trial_workers[i].join()
            for i in trial_workers:
                self.proc_trial_data[trial_workers[i].trial_num] = trial_workers[i].proc_trial_data

        self.proc_trigger_data = {
            'config': {
                'data_indices': data_indices,
                'data_times': data_times,
                'data_errors': data_errors,
                'data_curr_prev': data_curr_prev,
                'name': self.getName(),
                'trigger': self.marker_name,
                'marker_inds': self.marker_inds,
                'marker_times': self.marker_times,
            },
            'trials': self.proc_trial_data
        }

        # Run the post processors.
        if self.config['trigger_post_processing']:
            if not trigger_processor:
                trigger_processor = TriggerProcessor()

            for config in self.config['trigger_post_processing']:
                if config['name'] in trigger_processor.post_processing.all:
                    trigger_processor.post_processing.all[config['name']](self.proc_trigger_data,
                                                                          config)

        if self.config['testing']:
            self.logger.send('INFO', self.getName() + ':  Avg. error: ' + str(sum(data_errors)/len(data_errors)),
                             os.getpid(), threading.get_ident())
