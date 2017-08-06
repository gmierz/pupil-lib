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


class PupilDatasets(CommonPupilData):
    def __init__(self, all_data):
        self.datasets = {}
        CommonPupilData.__init__(self, all_data, 'datasets')

    @CommonPupilData.data_type.setter
    def data_type(self, data_type):
        self._data_type = data_type

        for _, ds in self.datasets.items():
            ds.data_type = self._data_type

    @CommonPupilData.time_or_data.setter
    def time_or_data(self, val):
        self._time_or_data = val

        for _, ds in self.datasets.items():
            ds.time_or_data = self._time_or_data

    def save_csv(self, output_dir):
        print('Saving data into a csv file.')
        for _, dataset in self.datasets.items():
            dataset.save_csv()

    def get_csv(self):
        print('Getting csv file.')
        csv_files = {}
        for dname, dataset in self.datasets.items():
            csv_files[dname] = dataset.get_csv()
        return csv_files

    def get_matrix(self):
        print('Getting matrix.')
        dataset_mat = {}
        for dname, dataset in self.datasets.items():
            dataset_mat[dname] = dataset.get_matrix()
        return dataset_mat

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
        print('Saving data into a csv file.')
        for _, data in self.data_streams.items():
            data.save_csv(output_dir, name + '_dataset')

    def get_csv(self):
        print('Getting csv file.')
        csv_files = {}
        for dname, data in self.data_streams.items():
            csv_files[dname] = data.get_csv()
        return csv_files

    def get_matrix(self):
        print('Getting matrix.')
        datastream_mats = {}
        for dname, data in self.data_streams.items():
            datastream_mats[dname] = data.get_matrix()
        return datastream_mats

    def load(self, all_data=None):
        if all_data is not None:
            self.all_data = all_data

        data = self.all_data['data']
        for data_name, datastream in data.items():
            pd_stream = PupilDatastream(datastream, data_name)
            pd_stream.load()
            self.data_streams[data_name] = pd_stream


class PupilDatastream(CommonPupilData):
    def __init__(self, stream_data, data_name):
        self.triggers = {}
        self.data_name = data_name
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
        print('Saving data into a csv file.')
        for _, trigger in self.triggers.items():
            trigger.save_csv(output_dir, name + self.data_name)

    def get_csv(self):
        print('Getting csv file.')
        csv_files = {}
        for _, trigger in self.triggers.items():
            csv_files[trigger.name] = trigger.get_csv()

    def get_matrix(self):
        print('Getting matrix.')
        stream_mats = {}
        for _, trigger in self.triggers.items():
            stream_mats[trigger.name] = trigger.get_matrix()
        return stream_mats

    def load(self, all_data=None):
        if all_data is not None:
            self.all_data = all_data

        data = self.all_data['triggers']
        for trigger_name, trigger in data.items():
            pds_trigger = PupilTrigger(trigger, trigger_name)
            pds_trigger.load()
            self.triggers[trigger_name] = pds_trigger


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
        print('Saving data into a csv file.')
        fname = name + '_' + self.time_or_data + '_' + '_trigger_' + self.trigger_name + '.csv'
        with open(os.path.join(output_dir, fname), 'w+') as csv_output:
            csv_output.write(self.get_csv())

    def get_csv(self):
        # Depends on get matrix
        print('Getting csv file.')
        csv_file = ''
        mat = self.get_matrix()
        count = 0
        max_count = len(mat)
        for trial in mat:
            if count < max_count - 1:
                csv_file += trial.join(',') + '\n'
            else:
                csv_file += trial.join(',')

        return csv_file

    def get_matrix(self):
        print('Getting matrix.')
        pupil_matrix = []
        for trial in self.trials:
            print(trial.get_matrix())
            pupil_matrix.append(trial.get_matrix())
        return pupil_matrix

    def load(self, all_data=None):
        if all_data is not None:
            self.all_data = all_data

        data = self.all_data['trials']
        for trial_num, trial in data.items():
            pdst_trial = PupilTrial(trial, int(trial_num))
            pdst_trial.load()
            self.trials.append(pdst_trial)


class PupilTrial(CommonPupilData):
    def __init__(self, trial_data, trial_num):
        self.trial_num = trial_num

        # Each of these are later filled with two
        # fields: data, and timestamps.
        self.__original_data = {}
        self.__baserem_data = {}
        self.__pc_data = {}
        self._proc_data = {'data': [], 'timestamps': []}         # Set to original data when loaded in load()

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
        return self._proc_data[self.time_or_data]

    @proc_data.setter
    def proc_data(self, data):
        self._proc_data[self.time_or_data] = data

    def save_csv(self, output_dir, name=''):
        print('Saving data into a csv file.')
        fname = name + '_' + self.time_or_data + '_' + 'trial_' + str(self.trial_num) + '.csv'
        with open(os.path.join(output_dir, fname), 'w+') as csv_output:
            csv_output.write(self.get_csv())

    def get_csv(self):
        # Depends on get matrix
        print('Getting csv file.')
        return self.get_matrix().join(',')

    def get_matrix(self, data_type=None):
        if data_type is not None:
            self.data_type = data_type
        print(self.data_type)
        return {
            'original': self.__original_data[self.time_or_data],
            'proc': self._proc_data[self.time_or_data],
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
