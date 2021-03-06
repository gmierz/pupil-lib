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
import argparse
import copy
import math
import sys
import warnings
import os

import ruamel.yaml as yaml
from pupillib.core.workers.processors.dataset_processor import DatasetDefaults
from pupillib.core.workers.processors.eye_processor import EyeDefaults
from pupillib.core.workers.processors.trial_processor import TrialDefaults

from pupillib.core.workers.processors.trigger_processor import TriggerDefaults

warnings.simplefilter('ignore', yaml.UnsafeLoaderWarning)


DEFAULT_PROCESSING = [{'name': 'default', 'config': []}]
DEFAULT_DATA_STREAMS = ['eye0', 'eye1', 'gaze_x', 'gaze_y']


class PLibParser(object):
    def __init__(self):
        self.parser = None
        self.config = None

    def get_parser(self):
        parser = argparse.ArgumentParser(description='Process Pupil-Lib data into trials through the use of \n'
                                                     'markers obtained from either LSL or the native marker \n'
                                                     'producer.')
        parser.add_argument('--datasets', '-D', type=str, nargs='*',
                            help='Datasets to process. Either this flag or the --proc-datasets must be used.')
        parser.add_argument('--proc-datasets', '-P', type=str, nargs='*',
                            help='Previously processed datasets to be used. Either this flag or the --datasets \n'
                                 'must be used.')
        parser.add_argument('--max-workers', '-MW', type=int, action='store', nargs=1,
                            help='Max number of workers that can be used.')
        parser.add_argument('--store', '-s', type=str, action='store', nargs=1,
                            help='Path to store data in. Metadata is stored in a pickled json file called \n'
                                 'data_state.json and alongside it is a folder that contains the raw data \n'
                                 'and broken down data for each of the epochs.')
        parser.add_argument('--dataset-pre-processing', type=yaml.load, nargs='*',
                            help='List of functions that should be run before epoching the dataset. These' +
                                 'are defined in the file dataset_processor.py.')
        parser.add_argument('--eye-pre-processing', type=yaml.load, nargs='*',
                            help='List of functions that should be run before epoching an eye. These' +
                                 'are defined in the file eye_processor.py.')
        parser.add_argument('--trigger-pre-processing', type=yaml.load, nargs='*',
                            help='List of functions that should be run before epoching a trigger. These' +
                                 'are defined in the file eye_processor.py.')
        parser.add_argument('--trial-pre-processing', type=yaml.load, nargs='*',
                            help='List of functions that should be run on the data chunk before a trial ' +
                                 'worker segments the trial from the data streams. '
                                 'are defined in the file eye_processor.py.')
        parser.add_argument('--dataset-post-processing', type=yaml.load, nargs='*',
                            help='List of functions that should be run after epoching the dataset. These' +
                                 'are defined in the file dataset_processor.py.')
        parser.add_argument('--eye-post-processing', type=yaml.load, nargs='*',
                            help='List of functions that should be run after epoching an eye. These' +
                                 'are defined in the file eye_processor.py.')
        parser.add_argument('--trigger-post-processing', type=yaml.load, nargs='*',
                            help='List of functions that should be run after epoching a trigger. These' +
                                 'are defined in the file eye_processor.py.')
        parser.add_argument('--trial-post-processing', type=yaml.load, nargs='*',
                            help='List of functions that should be run on the data chunk after a trial ' +
                                 'worker segments the trial from the data streams. '
                                 'are defined in the file eye_processor.py.')
        parser.add_argument('--trial-range', '-tr', type=int, action='append', nargs=2,
                            help='The trial range to extract for the given trigger names. The first number given\n'
                                 'is assumed to be the number of seconds before the before the triggers and the \n'
                                 'second number is the number of seconds after the triggers.')
        parser.add_argument('--baseline', '-b', type=float, action='store', nargs=2,
                            help='The time bounds that should be considered as a baseline \n'
                                 'for the trial. If it is not specified, pupil-lib will not produce a dataset \n'
                                 'that has baseline means removed and neither will it produce a dataset that has\n'
                                 'a percent change representation of the data.')
        parser.add_argument('--triggers', '-t', type=str, nargs='+',
                            help='The names of the triggers to process. Use --trigger-trials to give a list of \n'
                                 'triggers and a time span for each of them.')
        parser.add_argument('--logger', '-lg', type=str, nargs=1,
                            help='By default, a log is saved in `core/logs/log` and this flag can change where the \n'
                                 'log will go. Currently, there are two options: \n'
                                 '          1 - default\n'
                                 '          2 - stdout\n'
                                 'Add a new handler to resources logger_config.json to have more options. It will \n'
                                 'become available through this flag.')
        parser.add_argument('--test', action='store_true',
                            help='This specifies if the output should be tested. Consider this as `debug` mode')
        parser.add_argument('--testingdepth', type=str, nargs=1,
                            help='By default, a low amount of depth will be output during testing. If more is needed'
                                 'set it to `deep`. For now, it`s all or nothing.')
        parser.add_argument('--run-config', '-rc', type=str, nargs=1,
                            help='A run configuration (YAML, .yml) that lets you specify specific processing (pre, '
                            'and post) functions at each level of processing. See the docs for information and '
                            ' examples of how this configuration file should be specified. Using this argument '
                            ' overrides all the other options.')
        parser.add_argument('--data-names', type=str, nargs='*',
                            help='Must be given if an xdf dataset is used. This specifies which data fields you are '
                                 'interested in. For example giving `eye0`, and `eye1` will give you the diameters of '
                                 'the eyes. There will be more...')
        parser.add_argument('--only-markers-in-streams', action='store_true', default=False,
                            help='This specifies if only the marker positions in the streams should be returned.')
        parser.add_argument('--save-mat', action='store_true', default=False,
                            help='If this flag is supplied, `.mat` files will be saved instead of `.csv` when running '
                                 'from CLI.')
        parser.add_argument('--prefix', type=str, default='',
                            help='If this flag is supplied, all files saved when running from CLI will be prefixed '
                                 'with this string.')
        self.parser = parser
        return parser

    '''
        Use this function to parse the arguments given through the command line interface
        and produce the configuration that will be used for decision making in the
        epoching process.
    '''
    def build_config_from_cli(self, args):
        self.config = {}
        if 'parsed_yaml' not in self.config:
            self.config['parsed_yaml'] = {}

        # Make sure there is some data to be ingested.
        if args.datasets is not None:
            self.config['proc_datasets'] = []
            for dataset_path in args.datasets:
                self.config['datasets'].append(os.path.abspath(dataset_path))
            self.config['processing_old'] = False
        elif args.proc_datasets is not None:
            self.config['proc_datasets'] = []
            for dataset_path in args.datasets:
                self.config['proc_datasets'].append(os.path.abspath(dataset_path))
            self.config['processing_old'] = True
        else:
            raise Exception('ERROR: Missing datasets. See `--help` for help with `--datasets` and `--proc-datasets`')

        # Get all the other arguments, let everything else take care
        # of errors in what it needs.
        self.config['max_workers'] = args.max_workers[0] if args.max_workers is not None else None
        self.config['store'] = args.store[0] if args.store is not None else None
        self.config['trial_range'] = args.trial_range[0] if args.trial_range is not None else None
        self.config['baseline'] = args.baseline[0] if args.baseline is not None else None
        self.config['logger'] = args.logger[0] if args.logger is not None else None
        self.config['triggers'] = args.triggers if args.triggers is not None else None
        self.config['logger'] = args.logger[0] if args.logger is not None else 'default'
        self.config['testing'] = args.test if args.test is not None else False
        self.config['testing_depth'] = args.testingdepth[0] if args.testingdepth is not None else 'low'
        self.config['only_markers_in_streams'] = args.only_markers_in_streams

        # If this is set to anything else, there must be a loader for the combination of fields.
        # Request these or build them yourself in xdfloader_processor.py.
        self.config['dataname_list'] = args.data_names if args.data_names is not None else DEFAULT_DATA_STREAMS

        # Always set defaults.

        # TODO: Use custom type to split pre and post processing functions
        # TODO: in the arguments.
        self.config['dataset_pre_processing'] = DEFAULT_PROCESSING if args.dataset_pre_processing is None \
            else args.dataset_pre_processing
        self.config['eye_pre_processing'] = DEFAULT_PROCESSING if args.eye_pre_processing is None \
            else args.eye_pre_processing
        self.config['trigger_pre_processing'] = DEFAULT_PROCESSING if args.trigger_pre_processing is None \
            else args.trigger_pre_processing
        self.config['trial_pre_processing'] = DEFAULT_PROCESSING if args.trial_pre_processing is None \
            else args.trial_pre_processing

        self.config['dataset_post_processing'] = DEFAULT_PROCESSING if args.dataset_post_processing is None \
            else args.dataset_post_processing
        self.config['eye_post_processing'] = DEFAULT_PROCESSING if args.eye_post_processing is None \
            else args.eye_post_processing
        self.config['trigger_post_processing'] = DEFAULT_PROCESSING if args.trigger_post_processing is None \
            else args.trigger_post_processing
        self.config['trial_post_processing'] = DEFAULT_PROCESSING if args.trial_post_processing is None \
            else args.trial_post_processing

        return self.config

    def build_config_from_yaml(self, args, yaml_path=None):
        print('Building config from yml file...')
        self.config = {}
        self.config['parsed_yaml'] = {}

        if yaml_path:
            data_to_load = yaml_path
        else:
            data_to_load = args.run_config[0]

        # Load the yaml config and parse it.
        with open(data_to_load, 'r') as stream:
            data_loaded = yaml.safe_load(stream)

        # There is nothing that verifies the YAML structure because
        # it is highly variable. So, we do our best here.

        yaml_config = data_loaded['config'] if 'config' in data_loaded else None

        def check_and_get(data_dict, field_name, default):
            val_to_return = default
            if data_dict:
                if field_name in data_dict:
                    val_to_return = data_dict[field_name]
            return val_to_return

        # If the yaml has group-wide configurations set
        # them through the 'config' field.
        self.config['max_workers'] = check_and_get(yaml_config, 'workers', None)
        self.config['logger'] = check_and_get(yaml_config, 'logger', 'default')
        self.config['store'] = check_and_get(yaml_config, 'output_dir', os.getcwd())
        self.config['trial_range'] = [check_and_get(yaml_config, 'baseline_time', None),
                                      check_and_get(yaml_config, 'trial_time', None)]
        self.config['baseline_time'] = check_and_get(yaml_config, 'baseline_time', None)
        self.config['baseline'] = check_and_get(yaml_config, 'baseline', None)
        self.config['trial_time'] = check_and_get(yaml_config, 'trial_time', None)
        self.config['triggers'] = check_and_get(yaml_config, 'triggers', None)
        # Testing is still specified from the command line.
        self.config['testing'] = check_and_get(yaml_config, 'testing', None)
        self.config['testing_depth'] = check_and_get(yaml_config, 'testing_depth', 'low')
        self.config['only_markers_in_streams'] = check_and_get(yaml_config, 'only_markers_in_streams', False)

        # Always set default processing functions unless given an empty list.
        # Pre-processing
        self.config['dataset_pre_processing'] = check_and_get(yaml_config, 'dataset_pre_processing',
                                                              DEFAULT_PROCESSING)

        self.config['eye_pre_processing'] = check_and_get(yaml_config, 'eye_pre_processing', DEFAULT_PROCESSING)

        self.config['trigger_pre_processing'] = check_and_get(yaml_config, 'trigger_pre_processing',
                                                              DEFAULT_PROCESSING)

        self.config['trial_pre_processing'] = check_and_get(yaml_config, 'trial_pre_processing', DEFAULT_PROCESSING)

        # Post-processing
        self.config['dataset_post_processing'] = check_and_get(yaml_config, 'dataset_post_processing',
                                                               DEFAULT_PROCESSING)

        self.config['eye_post_processing'] = check_and_get(yaml_config, 'eye_post_processing', DEFAULT_PROCESSING)

        self.config['trigger_post_processing'] = check_and_get(yaml_config, 'trigger_post_processing',
                                                               DEFAULT_PROCESSING)

        self.config['trial_post_processing'] = check_and_get(yaml_config, 'trial_post_processing',
                                                             DEFAULT_PROCESSING)

        self.config['dataname_list'] = check_and_get(yaml_config, 'data_names', DEFAULT_DATA_STREAMS)

        # If the trial range and triggers, were not declared in the
        # config section, then they must either be declared in the
        # dataset, or eye sections. For each dataset, keep a list of triggers
        # and union them as we find new references so that we don't discard
        # any of them. If either dataset has None as it's set of triggers
        # an error will be raised.
        all_info = {}
        default_triggers = self.config['triggers'] if 'triggers' in self.config else None

        # A couple helper functions.
        def get_latest_default(old_default, dict_with_new, field):
            if field in dict_with_new:
                return dict_with_new[field]
            return old_default

        def union(a, b):
            if a:
                return list(set().union(a, b))
            return b

        def replace_keys(given_config, defaults_config):
            new_config = {}

            for key in defaults_config:
                new_config[key] = copy.deepcopy(get_latest_default(defaults_config[key], given_config, key))
            '''
            for key in given_config:
                if key not in defaults_config:
                    new_config[key] = given_config[key]
            '''

            return new_config

        dataset_names = []
        data_name_per_dataset = {}
        for dataset_name in data_loaded:
            if dataset_name != 'config':

                # Default is what is given in 'config' field.
                dataset_default_triggers = default_triggers

                # Process a dataset configuration.
                dataset_config = data_loaded[dataset_name]

                # Use path as the dict entries. Must always be given.
                if 'dataset_path' in dataset_config:
                    dataset_path = os.path.abspath(
                        dataset_config['dataset_path']
                    ).replace('\\', os.path.sep).replace('/', os.path.sep)
                else:
                    raise Exception("Error: Path to data folder must be given.")

                dataset_config_name = dataset_name + '|' + dataset_path
                data_name_per_dataset[dataset_config_name] = []
                dataset_names.append(dataset_config_name)

                # If we find a trigger field in the datatset config,
                # set it as the new default for the entire dataset.
                # Otherwise, leave it to what the config set it as.
                # Do this for baseline_time and trial_time as well.
                dataset_info = replace_keys(dataset_config, self.config)
                dataset_info['trial_range'] = [dataset_info['baseline_time'], dataset_info['trial_time']]

                # If no data names are specified, check for an additional list or
                # assume the eye diameters by default.
                if 'data_names' in dataset_config:
                    data_name_per_dataset[dataset_config_name] = dataset_config['data_names']
                elif 'datasets' in dataset_config:
                    data_name_per_dataset[dataset_config_name] = list(dataset_config['datasets'].keys())
                else:
                    print("Using default set of data streams: %s" % dataset_info['dataname_list'])
                    data_name_per_dataset[dataset_config_name] = dataset_info['dataname_list']

                # Now, go through the data names specified, if there
                # are none, eye0 and eye1 will be used as default.
                if 'datasets' in dataset_config:
                    for data_name in dataset_config['datasets']:
                        eye_default_triggers = dataset_info['triggers']

                        eye_config = dataset_config['datasets'][data_name]
                        data_name_per_dataset[dataset_config_name] = union([data_name],
                                                                           data_name_per_dataset[dataset_config_name])
                        eye_config_name = dataset_config_name + ":" + data_name

                        # Get the newest settings for this eye
                        eye_info = replace_keys(eye_config, dataset_info)

                        # Sets the triggers to a new list.
                        eye_default_triggers = get_latest_default(eye_default_triggers, eye_config,
                                                                  'triggers-list')
                        eye_info['triggers'] = eye_default_triggers
                        eye_info['trial_range'] = [eye_info['baseline_time'], eye_info['trial_time']]

                        # More specific functions for some trigger (may or may not be listed in
                        # 'triggers_list').
                        if 'triggers' in eye_config:
                            for trigger_name in eye_config['triggers']:
                                # For each trigger name, union it with the list of already running
                                # triggers specified in eye_info['triggers'] - in case of differences.
                                eye_info['triggers'] = union(eye_info['triggers'], [trigger_name])

                                trigger_config = eye_config['triggers'][trigger_name]
                                trigger_config_name = eye_config_name + ":trigger" + trigger_name

                                # Get the newest settings for this trigger, if any.
                                trigger_info = replace_keys(trigger_config, eye_info)

                                trigger_info['only_markers_in_streams'] = self.config['only_markers_in_streams']
                                trigger_info['trial_range'] = [trigger_info['baseline_time'], trigger_info['trial_time']]

                                if 'trials' in trigger_config:
                                    for trial_num in trigger_config['trials']:
                                        trial_config = trigger_config['trials'][trial_num]
                                        trial_config_name = trigger_config_name + ":trial" + str(trial_num)

                                        # Get the newest settings for this trial, if any.
                                        trial_info = replace_keys(trial_config, trigger_info)
                                        trial_info['trial_range'] = [trial_info['baseline_time'], trial_info['trial_time']]

                                        if trial_info['trial_time'] is None:
                                            raise Exception("Error: No trial time was given for " +
                                                            trial_config_name + " at: " + dataset_path)
                                        elif trial_info['baseline_time'] is None:
                                            raise Exception("Error: No baseline time was given for " +
                                                            trial_config_name + " at: " + dataset_path)

                                        all_info[trial_config_name] = copy.deepcopy(trial_info)

                                all_info[trigger_config_name] = copy.deepcopy(trigger_info)

                        # If the eye triggers are empty, then it means triggers were missing either
                        # in this field or above in the dataset, or config fields.
                        if not eye_info['triggers']:
                            raise Exception(
                                "Error: No triggers were given for " + dataset_name + " at: " + dataset_path)

                        all_info[eye_config_name] = copy.deepcopy(eye_info)
                if len(data_name_per_dataset[dataset_config_name]) == 0:
                    data_name_per_dataset[dataset_config_name] = ['eye0', 'eye1']

                all_info[dataset_config_name] = copy.deepcopy(dataset_info)
        # If no datasets were found.
        if not all_info:
            raise Exception("Error: No datasets given.")

        self.config['datasets'] = dataset_names
        self.config['data_name_per_dataset'] = data_name_per_dataset
        self.config['parsed_yaml'] = all_info

        if yaml_path:
            self.config = self.parse_processing_defaults(self.config)

    def parse_processing_defaults(self, data_dict):
        def choose_defaults(level, position):
            return {
                'dataset': {
                    'pre_processing': DatasetDefaults.pre_defaults(),
                    'post_processing': DatasetDefaults.post_defaults(),
                },
                'eye': {
                    'pre_processing': EyeDefaults.pre_defaults(),
                    'post_processing': EyeDefaults.post_defaults(),
                },
                'trigger': {
                    'pre_processing': TriggerDefaults.pre_defaults(),
                    'post_processing': TriggerDefaults.post_defaults(),
                },
                'trial': {
                    'pre_processing': TrialDefaults.pre_defaults(),
                    'post_processing': TrialDefaults.post_defaults(),
                },
            }[level][position]

        def replace_default_in_list(proc_list, new_defaults):
            new_proc_list = []
            for proc in proc_list:
                if proc['name'] == 'default':
                    new_proc_list += new_defaults
                else:
                    new_proc_list.append(proc)
            return new_proc_list

        new_dict = data_dict
        for entry in data_dict:
            if '_pre_processing' in entry or '_post_processing' in entry:
                for functs in data_dict[entry]:
                    if 'default' in functs['name']:
                        defaults = choose_defaults(entry.split('_')[0], '_'.join(entry.split('_')[1:]))
                        new_dict[entry] = replace_default_in_list(data_dict[entry], defaults)
                        break
            elif isinstance(data_dict[entry], dict):
                new_dict[entry] = self.parse_processing_defaults(data_dict[entry])

        return new_dict

    def build_config(self, args):
        # Determine if we build from parser options
        # or from yaml options.
        if args.run_config is not None:
            self.build_config_from_yaml(args)
        else:
            self.build_config_from_cli(args)

        # Store some optional CLI arguments here,
        # these are only used when pupillib is used
        # from the command line.
        self.config['save_mat'] = False
        self.config['prefix'] = ''
        if args.save_mat:
            self.config['save_mat'] = True
        if args.prefix:
            self.config['prefix'] = args.prefix

        self.config = self.parse_processing_defaults(self.config)

    '''
        Run this function determine the maximum worker count. Here, we assume that each
        trigger worker must process all trials for the sake of simplicity. It is changed
        later in the loader to a more specific value.
    '''
    def get_worker_count(self):
        # In total, there are 2*n*x processes that can spawn, where n
        # is the number of datasets and x is the number of trials across
        # all triggers. This can be changed with '--max-workers'.

        # Get max dataset workers and if we are processing old or new datasets.
        # It's one or the other and not both.
        if self.config['datasets'] is not None:
            num_datasets = len(self.config['datasets'])
        else:
            num_datasets = len(self.config['proc_datasets'])

        # Set a flag for if we are processing old or new datasets.

        num_datasets_per_worker = num_datasets
        num_dataset_workers = 1

        # Get eye workers.
        num_eyes = num_datasets * 2
        num_eyes_per_worker = num_eyes
        num_eye_workers = 0

        # Get max trigger workers.
        total_triggers = len(self.config['triggers'])*num_eyes
        num_triggers = len(self.config['triggers'])
        num_triggers_per_worker = total_triggers
        num_trigger_workers = 0

        max_workers = self.config['max_workers'] if self.config['max_workers'] is not None else -1

        self.config['maximize'] = False
        total_possible_workers = num_datasets + (num_datasets * 2) + (num_datasets * num_triggers * 2)
        if max_workers == -1 or max_workers >= total_possible_workers:
            # Set the maximums
            num_dataset_workers = num_datasets
            num_datasets_per_worker = 1

            num_eye_workers = num_eyes
            num_eyes_per_worker = 1

            num_trigger_workers = total_triggers
            num_triggers_per_worker = 1

            self.config['leftover_workers'] = 0
            self.config['total_workers'] = total_possible_workers

            self.config['num_datasets'] = num_datasets
            self.config['dataset_workers'] = num_dataset_workers
            self.config['datasets_per_worker'] = num_datasets_per_worker

            self.config['num_eyes'] = num_eyes
            self.config['eye_workers'] = num_eye_workers
            self.config['eyes_per_worker'] = num_eyes_per_worker

            self.config['total_triggers'] = total_triggers
            self.config['num_triggers'] = num_triggers
            self.config['trigger_workers'] = num_trigger_workers
            self.config['triggers_per_worker'] = num_triggers_per_worker

            # May or may not be used.
            self.config['num_trials'] = sys.maxsize
            self.config['trial_workers'] = sys.maxsize
            self.config['trials_per_worker'] = 1

            self.config['maximize'] = True
            return self.config
        elif self.config['max_workers'] == 1 or self.config['max_workers'] == 0:
            if self.config['max_workers'] == 0:
                self.config['max_workers'] = 1
            # If 'no_parallel' is set, other fields will never be
            # checked.
            self.config['no_parallel'] = True
            self.config['worker_count_complete'] = True
            self.config['num_datasets'] = num_datasets
            self.config['num_eyes'] = num_eyes
            self.config['num_triggers'] = num_triggers
            self.config['total_triggers'] = total_triggers
            return self.config

        # Otherwise, we have to do some splitting.
        # To make sure we don't make odd splitting decisions
        # and to keep the splits "even" we will generously underestimate
        # at certain times.
        if self.config['max_workers'] < num_datasets:
            # Leave everything else as zero and spread the work across dataset workers.
            num_datasets_per_worker = math.ceil(num_datasets/self.config['max_workers'])
            num_dataset_workers = self.config['max_workers']
        elif num_datasets < self.config['max_workers'] < num_eyes + num_datasets:
            # Give each dataset a worker.
            num_dataset_workers = num_datasets
            num_datasets_per_worker = 1

            # Split the remaining across the eye workers.
            curr_max_workers = self.config['max_workers'] - num_datasets
            if curr_max_workers > num_datasets:
                # We have enough to make a 'good enough' split.
                # i.e. we won't reduce the number of processes
                num_eyes_per_worker = math.ceil(num_eyes/curr_max_workers)
                num_eye_workers = curr_max_workers
        elif num_eyes+num_datasets < self.config['max_workers'] \
                < num_eyes + num_datasets + (num_datasets*num_triggers*2):
            # Give each dataset, and eye a worker.
            num_dataset_workers = num_datasets
            num_datasets_per_worker = 1

            num_eye_workers = num_eyes
            num_eyes_per_worker = 1

            # Split the remaining across the trigger workers.
            curr_max_workers = self.config['max_workers'] - num_datasets - num_eyes
            if curr_max_workers > num_eyes:
                # We have enough to make a 'good enough' split.
                # i.e. we won't reduce the number of processes
                num_triggers_per_worker = math.ceil(total_triggers/curr_max_workers)
                num_trigger_workers = curr_max_workers
        else:
            # We have enough to split the work across all of them and maybe
            # some extra for processing the trials.

            # Give each dataset, eye, and trigger a worker.
            num_dataset_workers = num_datasets
            num_datasets_per_worker = 1

            num_eye_workers = num_eyes
            num_eyes_per_worker = 1

            num_trigger_workers = total_triggers
            num_triggers_per_worker = 1
            self.config['leftover_workers'] = self.config['max_workers'] - \
                num_eyes + num_datasets + (num_datasets * num_triggers * 2)

        self.config['ideal_num_workers'] = total_possible_workers
        self.config['total_workers'] = num_dataset_workers + num_eye_workers + num_trigger_workers

        self.config['num_datasets'] = num_datasets
        self.config['dataset_workers'] = num_dataset_workers
        self.config['datasets_per_worker'] = num_datasets_per_worker

        self.config['num_eyes'] = num_eyes
        self.config['eye_workers'] = num_eye_workers
        self.config['eyes_per_worker'] = num_eyes_per_worker

        self.config['total_triggers'] = total_triggers
        self.config['num_triggers'] = num_triggers
        self.config['trigger_workers'] = num_trigger_workers
        self.config['triggers_per_worker'] = num_triggers_per_worker

        # May or may not be used.
        self.config['num_trials'] = sys.maxsize
        self.config['trial_workers'] = sys.maxsize
        self.config['trials_per_worker'] = 1
        if 'parsed_yaml' not in self.config:
            self.config['parsed_yaml'] = {}
        return self.config


def update_worker_count_with_trials(config, num_trials):
    """
        After the number of trials is determined, update the worker count
        to know how many processes can be used on the trials.
    """

    # Set this for the sake of convenience
    config['num_trials'] = num_trials

    if not config['worker_count_complete']:
        # If we haven't already run out of workers, split them across the trigger processes.
        if config['max_workers'] is not None:
            leftover = config['leftover_workers']

            if leftover != 0:
                # If we have some workers left over, split them among the trigger workers.
                total_trigger_workers = config['dataset_workers']*config['trigger_workers']
                total_trial_workers = total_trigger_workers*num_trials

                if leftover < total_trial_workers:
                    # We don't have enough to let each trial have a process.
                    config['trial_workers'] = math.floor(leftover/total_trigger_workers) \
                                                if math.floor(leftover / total_trigger_workers) > 0 \
                                                else 1
                    config['trials_per_worker'] = math.floor(num_trials/config['trial_workers'])

                    return config
                # Otherwise, we have enough to continue normally with the max number of processes.
        config['trial_workers'] = num_trials
        config['trials_per_worker'] = 1
    return config
