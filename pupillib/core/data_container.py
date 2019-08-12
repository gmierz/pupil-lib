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
import copy

from pupillib.core.utilities.MPLogger import MultiProcessingLog
logger = MultiProcessingLog.get_logger()

def common_get_csv(mat):
    csv_file = ''
    count = 0
    max_count = len(mat)
    if type(mat[0]) not in (list, dict):
        mat = [mat]
    for row in mat:
        if count < max_count - 1:
            csv_file += ",".join(map(str, row)) + '\n'
        else:
            csv_file += ",".join(map(str, row))
    return csv_file


sio = None
def common_save_mat(data, fname):
    global sio
    if not sio:
        try:
            import scipy.io as sio1
            sio = sio1
        except ImportError:
            raise Exception(
                "Cannot save data as .MAT file because the `scipy` package is not installed.\n"
                "Run `pip install scipy` to install it (not a required package for pupillib)"
            )
    sio.savemat(fname, data)


class CommonPupilData:
    def __init__(self, all_data, name):

        # Can be 'original', 'proc', 'baserem', 'pc'
        self.data_type = 'original'

        # Can be 'timestamps' or 'data'
        self.time_or_data = 'data'

        self.name = name
        self.all_data = all_data

    @property
    def data_type(self):
        return self._data_type

    @data_type.setter
    def data_type(self, data_type):
        self._data_type = data_type

    @property
    def time_or_data(self):
        return self._time_or_data

    @time_or_data.setter
    def time_or_data(self, val):
        self._time_or_data = val

    def load(self, all_data=None):
        self.all_data = all_data

    def destroy_all_data(self):
        self.all_data = None


class PupilDatasets(CommonPupilData):
    def __init__(self, config, all_data):
        self.config = config

        try:
            srate = all_data['datasets'][list(all_data['datasets'].keys())[0]]['config']['srate']
            self.srate = round(srate, 0)
            logger.send(
                "WARNING",
                "Using {} as sampling rate - ".format(self.srate) +\
                "be careful with this value if it varies across datastreams."
            )
        except:
            logger.send("ERROR","Could not obtain sampling rate.")

        self.datasets = {}
        CommonPupilData.__init__(self, all_data, 'datasets')

    @CommonPupilData.data_type.setter
    def data_type(self, data_type):
        self._data_type = data_type

        for _, ds in self.datasets.items():
            if ds:
                ds.data_type = self._data_type

    @CommonPupilData.time_or_data.setter
    def time_or_data(self, val):
        self._time_or_data = val

        for _, ds in self.datasets.items():
            if ds:
                ds.time_or_data = self._time_or_data

    def save_csv(self, output_dir, name=''):
        for _, dataset in self.datasets.items():
            if dataset:
                dataset.save_csv(output_dir, name=name)

    def save_trigger_csv(self, output_dir, name=''):
        for _, dataset in self.datasets.items():
            if dataset:
                dataset.save_trigger_csv(output_dir, name=name)

    def save_rawstream_csv(self, output_dir, name=''):
        for _, dataset in self.datasets.items():
            if dataset:
                dataset.save_rawstream_csv(output_dir, name=name)

    def get_csv(self):
        csv_files = {}
        for dname, dataset in self.datasets.items():
            if dataset:
                csv_files[dname] = dataset.get_csv()
        return csv_files

    def get_matrix(self):
        dataset_mat = {}
        for dname, dataset in self.datasets.items():
            if dataset:
                dataset_mat[dname] = dataset.get_matrix()
        return dataset_mat

    # If source_dset_name is defined, then we will take
    # a dataset from within this object and merge it into
    # target_dset_name. If dsets_object is defined then we
    # will take all streams, from all datasets, from that
    # object and merge them into target_dset_name.
    def merge(self, target_dset_name, source_dset_name=None, dsets_object=None, keep_raw=False):
        if target_dset_name not in self.datasets:
            raise Exception('Error merging: target_dset_name=' + target_dset_name + ' does not exist in this datastore object.')
        if not self.datasets[target_dset_name]:
            raise Exception(
                'Error merging: target_dset_name=' + target_dset_name + ' is None in this datastore object.')
        merge_into = self.datasets[target_dset_name]

        if source_dset_name:
            merge_src = self.datasets[source_dset_name]
            merge_into.merge(merge_src, keep_raw=keep_raw)
        elif dsets_object:
            for dsetname, dset in dsets_object.datasets.items():
                if not dset: continue;
                if dset.reject: continue;
                merge_into.merge(dset, keep_raw=keep_raw)
        else:
            new_dsets = {}
            for dset in self.datasets:
                if not self.datasets[dset]: continue
                if dset != target_dset_name:
                    merge_into.merge(self.datasets[dset], keep_raw=keep_raw)
                    self.datasets[dset] = None

        keys_to_del = []
        for key, dset in self.datasets.items():
            if not dset: keys_to_del.append(key)

        for key in keys_to_del:
            del self.datasets[key]

        self.datasets[target_dset_name] = merge_into

    # Suggested usage: Use entire dataset in loading and
    # don't load per trial by yourself. Otherwise, you will
    # need to know the data structure of the data obtained
    # and it's highly likely that it could change - breaking
    # your code.
    def load(self, all_data=None):
        if all_data is not None:
            self.all_data = all_data

        data = self.all_data['datasets']
        for dataset_name, dataset in data.items():
            pd = PupilDataset(dataset, dataset_name)
            pd.load()
            self.datasets[dataset_name] = pd
        self.destroy_all_data()

    def reject_datasets(self, dataset_names):
        for dataset in dataset_names:
            if dataset in self.datasets:
                self.datasets[dataset].reject = True

    def reject_trials(self, trials, trigger, datastream_names=[]):
        for _, dset in self.datasets.items():
            if not dset: continue
            dset.reject_trials(trials, trigger, datastream_names=datastream_names)

    def process_trials(self, func, **kwargs):
        for _, dset in self.datasets.items():
            if not dset: continue
            dset.process_trials(func, **kwargs)


class PupilDataset(CommonPupilData):
    def __init__(self, dataset, dataset_name):
        self.data_streams = {}
        self.dataset_name = dataset_name
        self.reject = False
        CommonPupilData.__init__(self, dataset, 'dataset')

    @CommonPupilData.data_type.setter
    def data_type(self, data_type):
        self._data_type = data_type

        for _, data in self.data_streams.items():
            data.data_type = self._data_type

    @CommonPupilData.time_or_data.setter
    def time_or_data(self, val):
        self._time_or_data = val

        for _, ds in self.data_streams.items():
            ds.time_or_data = self._time_or_data

    def save_csv(self, output_dir, name=''):
        for _, data in self.data_streams.items():
            data.save_csv(output_dir, name + '_' + self.dataset_name)

    def save_trigger_csv(self, output_dir, name=''):
        for _, data in self.data_streams.items():
            data.save_trigger_csv(output_dir, name + '_' + self.dataset_name)

    def save_rawstream_csv(self, output_dir, name=''):
        for _, data in self.data_streams.items():
            data.save_rawstream_csv(output_dir, name + '_' + self.dataset_name)

    def save_mat(self, output_dir, name=''):
        for _, data in self.data_streams.items():
            data.save_mat(output_dir, name + '_' + self.dataset_name)

    def save_trigger_mat(self, output_dir, name=''):
        for _, data in self.data_streams.items():
            data.save_trigger_mat(output_dir, name + '_' + self.dataset_name)

    def save_rawstream_mat(self, output_dir, name=''):
        for _, data in self.data_streams.items():
            data.save_rawstream_mat(output_dir, name + '_' + self.dataset_name)

    def get_csv(self):
        csv_files = {}
        for dname, data in self.data_streams.items():
            csv_files[dname] = data.get_csv()
        return csv_files

    def get_matrix(self):
        datastream_mats = {}
        for dname, data in self.data_streams.items():
            datastream_mats[dname] = data.get_matrix()
        return datastream_mats

    # Merges all data from dset_src into itself.
    def merge(self, dset_src, keep_raw=False):
        for data_name, datastream in dset_src.data_streams.items():
            if data_name in self.data_streams:
                self.data_streams[data_name].merge(datastream,  keep_raw=keep_raw)

    def load(self, all_data=None):
        if all_data is not None:
            self.all_data = all_data
        if 'data' not in self.all_data:
            return

        data = self.all_data['data']
        for data_name, datastream in data.items():
            pd_stream = PupilDatastream(datastream, data_name)
            pd_stream.load()
            self.data_streams[data_name] = pd_stream

        self.destroy_all_data()

    def reject_trials(self, trials, trigger, datastream_names=None):
        if datastream_names is None:
            datastream_names = []
        for data_name, datastream in self.data_streams.items():
            if datastream_names and data_name not in datastream_names:
                continue
            self.data_streams[data_name].reject_trials(trials, trigger)

    def process_trials(self, func, **kwargs):
        for _, datastream in self.data_streams.items():
            datastream.process_trials(func, **kwargs)


class PupilDatastream(CommonPupilData):
    def __init__(self, stream_data, data_name):
        self.triggers = {}
        self.data_name = data_name
        self.data = stream_data['config']['dataset']['data']
        self.timestamps = stream_data['config']['dataset']['timestamps']

        if stream_data['triggers']:
            self.trigger_names = [i for i in stream_data['triggers']]
        else:
            self.trigger_names = []

        if self.trigger_names:
            self.trigger_indices = {}
            self.trigger_times = {}
            for i in self.trigger_names:
                self.trigger_indices[i] = stream_data['triggers'][i]['data_indices']
                self.trigger_times[i] = stream_data['triggers'][i]['data_times']

        CommonPupilData.__init__(self, stream_data, 'datastream')

    @CommonPupilData.data_type.setter
    def data_type(self, data_type):
        self._data_type = data_type

        for _, trigger in self.triggers.items():
            trigger.data_type = self._data_type

    @CommonPupilData.time_or_data.setter
    def time_or_data(self, val):
        self._time_or_data = val

        for _, trigger in self.triggers.items():
            trigger.time_or_data = self._time_or_data

    def save_csv(self, output_dir, name=''):
        for _, trigger in self.triggers.items():
            trigger.save_csv(output_dir, name + '_' + self.data_name)

    def save_trigger_csv(self, output_dir, name=''):
        self.__save_trigger_csv(output_dir, name + '_' + self.data_name)

    def __save_trigger_csv(self, output_dir, name=''):
        for trigger_name in self.trigger_indices:
            fname = name + '_' + self.time_or_data + '_' + self.data_type + '_triggerindices_' + trigger_name + '.csv'
            with open(os.path.join(output_dir, fname), 'w+') as csv_output:
                csv_output.write(common_get_csv(self.trigger_indices[trigger_name]))
        for trigger_name in self.trigger_times:
            fname = name + '_' + self.time_or_data + '_' + self.data_type + '_triggertimes_' + trigger_name + '.csv'
            with open(os.path.join(output_dir, fname), 'w+') as csv_output:
                csv_output.write(common_get_csv(self.trigger_times[trigger_name]))

    def save_rawstream_csv(self, output_dir, name=''):
        fname = name + '_' + self.time_or_data + '_' + self.data_type + '_rawstream_' + self.data_name + '.csv'
        with open(os.path.join(output_dir, fname), 'w+') as csv_output:
            if self.time_or_data == 'data':
                csv_output.write(common_get_csv(self.data))
            else:
                csv_output.write(common_get_csv(self.timestamps))

    def save_mat(self, output_dir, name=''):
        for _, trigger in self.triggers.items():
            trigger.save_mat(output_dir, name + '_' + self.data_name)

    def save_trigger_mat(self, output_dir, name=''):
        self.__save_trigger_mat(output_dir, name + '_' + self.data_name)

    def __save_trigger_mat(self, output_dir, name=''):
        for trigger_name in self.trigger_indices:
            fname = name + '_' + self.time_or_data + '_' + self.data_type + '_triggerindices_' + trigger_name + '.mat'
            fname = os.path.join(output_dir, fname)
            common_save_mat(self.trigger_indices[trigger_name], fname)
        for trigger_name in self.trigger_times:
            fname = name + '_' + self.time_or_data + '_' + self.data_type + '_triggertimes_' + trigger_name + '.mat'
            fname = os.path.join(output_dir, fname)
            common_save_mat(self.trigger_times[trigger_name], fname)

    def save_rawstream_mat(self, output_dir, name=''):
        fname = name + '_' + self.time_or_data + '_' + self.data_type + '_rawstream_' + self.data_name + '.mat'
        fname = os.path.join(output_dir, fname)
        if self.time_or_data == 'data':
            common_save_mat(self.data, fname)
        else:
            common_save_mat(self.timestamps, fname)

    def get_csv(self):
        csv_files = {}
        for _, trigger in self.triggers.items():
            csv_files[trigger.name] = trigger.get_csv()

    def get_matrix(self):
        stream_mats = {}
        for _, trigger in self.triggers.items():
            stream_mats[trigger.name] = trigger.get_matrix()
        return stream_mats

    def merge(self, dstream_src, keep_raw=False):
        for trigger_name, trig_data in dstream_src.triggers.items():
            if trigger_name in self.triggers:
                if not keep_raw:
                    trig_data.data = None
                    trig_data.timestamps = None
                self.triggers[trigger_name].merge(trig_data)

    def load(self, all_data=None):
        if all_data is not None:
            self.all_data = all_data

        data = self.all_data['triggers']
        if not data:
            self.destroy_all_data()
            self.triggers = {}
            return

        for trigger_name, trigger in data.items():
            pds_trigger = PupilTrigger(trigger, trigger_name)
            pds_trigger.load()
            self.triggers[trigger_name] = pds_trigger

        self.destroy_all_data()

    def reject_trials(self, trials, trigger):
        for trigger_name, trig_data in self.triggers.items():
            if trigger_name != trigger:
                continue
            trig_data.reject_trials(trials)

    def process_trials(self, func, **kwargs):
        for _, trig_data in self.triggers.items():
            trig_data.process_trials(func, **kwargs)


class PupilTrigger(CommonPupilData):
    def __init__(self, trigger_data, trigger_name):
        self.trials = []
        self.trigger_name = trigger_name
        CommonPupilData.__init__(self, trigger_data, 'trigger')

    @CommonPupilData.data_type.setter
    def data_type(self, data_type):
        self._data_type = data_type

        for trial in self.trials:
            trial.data_type = self._data_type

    @CommonPupilData.time_or_data.setter
    def time_or_data(self, val):
        self._time_or_data = val

        for trial in self.trials:
            trial.time_or_data = self._time_or_data

    def save_csv(self, output_dir, name=''):
        fname = name + '_' + self.time_or_data + '_' + self.data_type + '_trigger_' + self.trigger_name + '.csv'
        with open(os.path.join(output_dir, fname), 'w+') as csv_output:
            csv_output.write(self.get_csv())

    def save_mat(self, output_dir, name=''):
        fname = name + '_' + self.time_or_data + '_' + self.data_type + '_trigger_' + self.trigger_name + '.mat'
        common_save_mat(self.get_matrix(), os.path.join(output_dir, fname))

    def get_csv(self):
        # Depends on get matrix
        csv_file = ''
        mat = self.get_matrix()
        count = 0
        max_count = len(mat)
        for trial in mat:
            if count < max_count - 1:
                csv_file += ",".join(map(str, trial)) + '\n'
            else:
                csv_file += ",".join(map(str, trial))

        return csv_file

    def get_matrix(self):
        pupil_matrix = []
        for trial in self.trials:
            if not trial.reject:
                pupil_matrix.append(trial.get_matrix())
        return pupil_matrix

    # Returns a matrix containing all trials regardless of
    # rejection status.
    def get_all_trials_matrix(self):
        pupil_matrix = []
        for trial in self.trials:
            pupil_matrix.append(trial.get_matrix())
        return pupil_matrix

    def merge(self, trigger_src):
        for trial in trigger_src.trials:
            self.trials.append(trial)

    def load(self, all_data=None):
        if all_data is not None:
            self.all_data = all_data

        data = self.all_data['trials']
        for trial_num, trial in data.items():
            pdst_trial = PupilTrial(trial, int(trial_num))
            pdst_trial.load()
            if trial['reject']:
                pdst_trial.reject = True
            self.trials.append(pdst_trial)

        self.destroy_all_data()

    def reject_trials(self, trial_nums):
        for num in trial_nums:
            self.trials[num-1].reject = True

    def process_trials(self, func, **kwargs):
        for trial in self.trials:
            trial.process_trial(func, **kwargs)


class PupilTrial(CommonPupilData):
    def __init__(self, trial_data, trial_num):
        self.trial_num = trial_num
        self.reject = False

        # Each of these are later filled with two
        # fields: data, and timestamps.
        self.__original_data = {'data': [], 'timestamps': []}
        self.__baserem_data = {'data': [], 'timestamps': []}
        self.__pc_data = {'data': [], 'timestamps': []}
        self.__proc_data = {'data': [], 'timestamps': []}         # Set to original data when loaded in load()

        CommonPupilData.__init__(self, trial_data, 'trial')

    @property
    def original_data(self):
        return self.__original_data[self.time_or_data]

    @property
    def baserem_data(self):
        return self.__baserem_data[self.time_or_data]

    @property
    def pc_data(self):
        return self.__pc_data[self.time_or_data]

    @property
    def proc_data(self):
        return self.__proc_data[self.time_or_data]

    @proc_data.setter
    def proc_data(self, data):
        self.__proc_data[self.time_or_data] = data

    def save_csv(self, output_dir, name=''):
        fname = name + '_' + self.time_or_data + '_' + self.data_type + '_' + 'trial_' + str(self.trial_num) + '.csv'
        with open(os.path.join(output_dir, fname), 'w+') as csv_output:
            csv_output.write(self.get_csv())

    def save_mat(self, output_dir, name=''):
        fname = name + '_' + self.time_or_data + '_' + self.data_type + '_' + 'trial_' + str(self.trial_num) + '.mat'
        common_save_mat(self.get_matrix(), os.path.join(output_dir, fname))

    def get_csv(self):
        # Depends on get matrix
        return ",".join(map(str, self.get_matrix()))

    def get_matrix(self, data_type=None):
        if data_type:
            self.data_type = data_type
        return {
            'original': self.__original_data[self.time_or_data],
            'proc': self.__proc_data[self.time_or_data],
            'baserem': self.__baserem_data[self.time_or_data],
            'pc': self.__pc_data[self.time_or_data]
        }[self.data_type]

    # Useful for when a processing function needs to be run multiple
    # times on the data, after running this once. Set data_type
    # to 'proc' to use this data array without affecting the original
    # data.
    def set_proc_to_original(self):
        self.proc_data = self.original_data

    def load(self, all_data=None):
        if all_data is not None:
            self.all_data = all_data

        self.__original_data = self.all_data['trial']
        self.__baserem_data = self.all_data['trial_rmbaseline']
        self.__pc_data = self.all_data['trial_pc']
        self.proc_data = copy.deepcopy(self.__original_data)

        self.destroy_all_data()

    def process_trial(self, func, **kwargs):
        data = func(self.get_matrix(), **kwargs)
        if type(data) in (bool,) and data == True:
            self.reject = True
        if type(data) not in (bool,):
            self.proc_data = data
            self.data_type = 'proc'
