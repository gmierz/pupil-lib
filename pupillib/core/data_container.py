import os
import copy

class CommonPupilData:
    def __init__(self, all_data, name):
        self.data_type = 'original'
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
            for dset in dsets_object.datasets.items():
                merge_into.merge(dset, keep_raw=keep_raw)
        else:
            for dset in self.datasets:
                if dset != target_dset_name:
                    merge_into.merge(self.datasets[dset], keep_raw=keep_raw)
                    self.datasets[dset] = None

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


class PupilDataset(CommonPupilData):
    def __init__(self, dataset, dataset_name):
        self.data_streams = {}
        self.dataset_name = dataset_name
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

        data = self.all_data['data']
        for data_name, datastream in data.items():
            pd_stream = PupilDatastream(datastream, data_name)
            pd_stream.load()
            self.data_streams[data_name] = pd_stream

        self.destroy_all_data()


class PupilDatastream(CommonPupilData):
    def __init__(self, stream_data, data_name):
        self.triggers = {}
        self.data_name = data_name
        self.data = stream_data['config']['dataset']['data']
        self.timestamps = stream_data['config']['dataset']['timestamps']
        self.trigger_names = [i for i in stream_data['triggers']]
        if self.trigger_names:
            self.trigger_indices = {}
            self.trigger_times = {}
            for i in self.trigger_names:
                self.trigger_indices[i] = stream_data['triggers'][i]['config']['data_indices']
                self.trigger_times[i] = stream_data['triggers'][i]['config']['data_times']
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
        for trigger_name, trigger in data.items():
            pds_trigger = PupilTrigger(trigger, trigger_name)
            pds_trigger.load()
            self.triggers[trigger_name] = pds_trigger

        self.destroy_all_data()


class PupilTrigger(CommonPupilData):
    def __init__(self, trigger_data, trigger_name):
        self.trials = []
        self.trigger_name = trigger_name
        self.rejected_trials = []
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
            mat = trial.get_matrix()
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
            if not trial['reject']:
                pdst_trial = PupilTrial(trial, int(trial_num))
                pdst_trial.load()
                self.trials.append(pdst_trial)
            else:
                pdst_trial = PupilTrial(trial, int(trial_num))
                pdst_trial.load()
                self.rejected_trials.append(pdst_trial)

        self.destroy_all_data()


class PupilTrial(CommonPupilData):
    def __init__(self, trial_data, trial_num):
        self.trial_num = trial_num

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
