# Data Container

The data container returned from a script call to `script_run(<YAML/CONFIG/PATH>` is a PupilLibRunner object with data
in the `.data_store` field. It has the following structure:

.data_store.datasets['dset_name'].data_stream['dstream_name'].triggers['trigger_name'].trials[0..N]

where N is the number of trials in that trigger. Each dataset object (i.e. .datasets['dset_name']), or any of the other
objects like .triggers['trigger_name'] have the following functions available to them:

    // Saves all the data into CSV files, broken down by datasets, streams, and triggers.
    // Individual trials can also be saved.
    // Change the flag `datatype` to `pc`, `original`, or `basrem` to get different
    // types of data saved.
    - save_csv(output_directory, name='')

    // Returns dictionaries at the datasets and data_stream level containing a matrix for
    // each of the triggers. Or simply a matrix at the trigger, and trial level. The
    // data_type argument can change the returned data from 'original', 'baserem', 'pc',
    // or 'proc'.
    - get_matrix(data_type=None)

    // Setting this value changes the values returned between timestamps, or data.
    - time_or_data = 'timestamps' or 'data'

    // Setting this value changes the type of data returned.
    - data_type = 'original', 'pc', 'baserem', or 'proc'

    // Merges datasets, data streams, or triggers. See data_container.py for more information.
    // .data_store
    - merge(target_dset_name, source_dset_name=None, dsets_object=None)

    // .datasets, .data_streams, .triggers
    - merge(data_source)

    // Use this to save trigger timestamps and names of each dataset
    // TODO: This is NOT IMPLEMENTED/FUNCTIONING for merged datasets
    - save_trigger_csv(output_dir, name='')

    // Use this to save the raw data stream to a csv
    // TODO: This is NOT IMPLEMENTED/FUNCTIONING for merged datasets
    - save_rawstream_csv(self, output_dir, name=''):

The following is a more detailed explanation:

        // Holds all the datasets.
        .data_store.datasets

            // Dictionary with keys being the names of datasets as defined through YAML config, i.e. from resources/test_yaml1.yml)
            // Each field is a PupilDataset object.
            - 'dataset1'
            - 'dataset2'
            - '...'

                .data_streams
                    // Dictionary with keys being the names of the data streams that were analyzed.
                    // These have a few fields.
                    - 'eye_0'
                    - 'eye_1'
                    - 'gaze_x'
                    - 'gaze_y'

                        .data // Raw data for this data stream.
                        .timestamp // Raw timestamps for this data stream.
                        .trigger_names // Array containing the names of the triggers in each data stream.

                        // These next two are dictionaries with fields that are the trigger names.
                        // i.e. trigger_indices[trigger_name[0]] are the indices for the first trigger.
                        .trigger_indices // Array of indices in the raw data that correspond to each marker.
                        .trigger_times // Exact times of each of the triggers.

                        .triggers
                            // Dictionary with keys being the trigger names.
                            - 'S11'
                            - '...'

                                .trials
                                    // Array of PupilTrial objects.
                                    // Each object has the following fields.
                                    .trial_num // The trial number.

                                    .original_data // The original data, shouldn't be modified.
                                    .proc_data // Defined as the original data, can be modified.
                                    .pc_data // Percent change data if the 'baseline' field is defined in the YAML config.
                                    .baserem_data // Data with the baseline removed, needs 'baseline' defined also.
