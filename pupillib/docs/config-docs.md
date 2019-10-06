## YAML Config Documentation


# Introduction

This type of configuration can be used for running specific parameters on different
portions of the data. They can either be specified at the dataset-specifc level, eye-specific,
trigger-specifc, or trial-specifc level. And furthermore, this can be set on any number of
datasets, regardless of previously being processed. For example, if you want to perform a specific
type of smoothing on a specific trial before it's placed into a trigger-wide data matrix, you can
specify it here. This tool also allows you to process multiple different triggers across any
number of datasets. You can use `test_yaml*.yml` as a template alongside the script `simple_script.py`.


# Schema

For earlier version of pupil lsl relay data (pre-2.0) anywhere you see things like 'eye0' (the data name),
you can swap in any option from this list:
    -- eye0
    -- eye1
    -- gaze_x
    -- gaze_y
    -- eye0-pyrep
    -- eye1-pyrep
    -- gaze_x-pyrep
    -- gaze_y-pyrep

The `pyrep` suffix allows you to get the data from the Pupil `Python representation` data streams.

When using version 2.0 (or later) of the pupil lsl relay, you will have access to all streams that
exist in the Gaze type stream called 'pupil_capture', they are listed here:
    -- confidence
    -- norm_pos_x
    -- norm_pos_y
    -- gaze_point_3d_x
    -- gaze_point_3d_y
    -- gaze_point_3d_z
    -- eye_center0_3d_x
    -- eye_center0_3d_y
    -- eye_center0_3d_z
    -- eye_center1_3d_x
    -- eye_center1_3d_y
    -- eye_center1_3d_z
    -- gaze_normal0_x
    -- gaze_normal0_y
    -- gaze_normal0_z
    -- gaze_normal1_x
    -- gaze_normal1_y
    -- gaze_normal1_z
    -- diameter0_2d
    -- diameter1_2d
    -- diameter0_3d
    -- diameter1_3d

The names that were available with version 1 are still available as a shorthand. They are mapped to
the following fields:
    -- eye0 -> diameter0_3d
    -- eye1 -> diameter1_3d
    -- gaze_x -> norm_pos_x
    -- gaze_y -> norm_pos_y
    -- eye0-pyrep -> diameter0_3d
    -- eye1-pyrep -> diameter1_3d
    -- gaze_x-pyrep -> norm_pos_x
    -- gaze_y-pyrep -> norm_pos_y

Note that when no data names are provided in the config file we default to obtaining the following data:
    -- eye0
    -- eye1
    -- gaze_x
    -- gaze_y

See `test_yaml3.yml` for an example config file for version 2+.

Below, is the structure of what is expected by the program when the '--run-config'
argument is given:

config:
    Optional(workers: <Int>)
    Optional(logger: AnyOf('default', 'stdout'))
    Optional But Recommended(
        output_dir: <String>
        -- Defaults to the current working directory returned by `os.getcwd()`.
    )
    Optional(trial_time: <Int>)
        -- Number of seconds to get after the event markers found for each trial
    Optional(baseline_time: <Int>)
        -- Number of seconds to get before the event markers found for each trial
    Optional(srate: <Float>)
        -- If this is set while using `custom_resample` from the trigger_post_processing
        -- configuration (as is the default) this sampling rate will be overwritten for
        -- the one given to `custom_resample` (this will be fixed in the future).
        -- To change this sampling rate, add the following entry in the `config`, or
        -- other post-processing definitions:
                - trigger_post_processing:
                    - name: custom_resample
                      config:
                        - srate: 60

    Optional(baseline: [<Float>, <Float>]
        -- Use the baseline flag to define the baseline range for each of the trials.
        -- i.e. [0, 1.5] means that we want the baseline to go from 0 to 1.5 seconds. where
        --      0 is defined as the first point of the trials.
        -- It can only be specified here for the time being.
        --
        -- If this flag is not supplied, no percent change calculations will be performed.
        -- This means that when `datastore.datatype` is set to `pc`, it will be empty.
    Optional(
        triggers:
            -- Names of triggers in each dataset.
            - <String>
            - <String>
            - ...
    )

    Optional(
        dataset_(pre and/or post)_processing:
            -- List of processing functions to run while epoching an entire dataset.
            -- For before (pre), use dataset_pre_processing, and for after (post)
            -- use dataset_post_processing. Use None in the list to indicate that no
            -- processing functions should be run. These lists are ordered, and that
            -- means that any item that is above another item, runs before the lower
            -- item.
            - <String>
            - <String>
            - ...
    )

    Optional(
        eye_(pre and/or post)_processing:
            -- List of processing functions to run before and after epoching an eye.
            -- For before (pre), use eye_pre_processing, and for after (post)
            -- use eye_post_processing. Use None in the list to indicate that no
            -- processing functions should be run. These lists are ordered, and that
            -- means that any item that is above another item, runs before the lower
            -- item.
            - <String>
            - <String>
            - ...
    )

    Optional(
        trigger_(pre and/or post)_processing:
            -- List of processing functions to run before and after epoching a trigger.
            -- For before (pre), use trigger_pre_processing, and for after (post)
            -- use trigger_post_processing. Use None in the list to indicate that no
            -- processing functions should be run. These lists are ordered, and that
            -- means that any item that is above another item, runs before the lower
            -- item.
            - <String>
            - <String>
            - ...
    )

    Optional(
        trial_(pre and/or post)_processing:
            -- List of processing functions to run before and after epoching a trial.
            -- For before (pre), use trial_pre_processing, and for after (post)
            -- use trial_post_processing. Use None in the list to indicate that no
            -- processing functions should be run. These lists are ordered, and that
            -- means that any item that is above another item, runs before the lower
            -- item.
            - <String>
            - <String>
            - ...
    )

    Optional(
        only_markers_in_streams: true/false (false by default)
            -- Set this to true to only extract the marker indices from the data, and
            -- to prevent trial extraction. It can also be used to speed up XDF to CSV
            -- conversion. See `example_only_get_marker_positions.py` and
            -- `example_xdf_to_csv.py` for examples on how this is used.
            --
            -- NOTE: These marker indices should be used on the raw datastreams that
            -- are stored in the datastore object.
    )

    **IMPORTANT**:
    Each pre/post processing stage can be disabled by adding the folowing to the list:
            - name: None
              config: None

    To set it to a function use this (for example):
            - name: filter_fft
              config:
                - highest_freq: 0.7
                - lowest_freq: 0

    If the default is still needed, you can put the following before or after an added function
    to ensure that the default settings are also run (in order from top to bottom):
            - name: default
              config: default


dataset_name:
    Required if not given in config field (
        dataset_path: <String>
        trial_time: <Double>                -- Used as default value
        baseline_time: <Double>             -- Used as default value
        processed: AnyOf(true, false)       -- Tells us if the dataset was already processed.
                                            -- Still needs default times if its been processed,
                                            -- specify them through the rest of the configuration.
    )

    Optional(
        dataset_(pre and/or post)_processing:
            - <String>
            - <String>
            - ...
    )

    Optional(
        eye_(pre and/or post)_processing:
            - <String>
            - <String>
            - ...
    )

    Optional(
        trigger_(pre and/or post)_processing:
            - <String>
            - <String>
            - ...
    )

    Optional(
        trial_(pre and/or post)_processing:
            - <String>
            - <String>
            - ...
    )

    Either (
        triggers:
            -- Name of the trigger
            - <String>
            - <String>
            - ...
    ) Or (
        -- It must be defined in the eyes
    )

    Optional (
        eye0:
            Optional(trial_time: <Int>)
            Optional(baseline_time: <Int>)

            Optional(
                eye_(pre and/or post)_processing:
                    - <String>
                    - <String>
                    - ...
            )

            Optional(
                trigger_(pre and/or post)_processing:
                    - <String>
                    - <String>
                    - ...
            )

            Optional(
                trial_(pre and/or post)_processing:
                    - <String>
                    - <String>
                    - ...
            )

            Required if not given in dataset_name (top-level) (
                triggers:
                    trigger_name:
                        Optional(trial_time: <Int>)
                        Optional(baseline_time: <Int>)

                        Optional(
                            trigger_(pre and/or post)_processing:
                                - <String>
                                - <String>
                                - ...
                        )

                        Optional(
                            trial_(pre and/or post)_processing:
                                - <String>
                                - <String>
                                - ...
                        )

                        Optional(
                            trials:
                                -- An integer number of the trial of it's
                                -- order in all trials in increasing order
                                -- by time.
                                trial_num:
                                    Optional(trial_time: <Int>)
                                    Optional(baseline_time: <Int>)
                                    Optional(
                                        trial_(pre and/or post)_processing:
                                            - <String>
                                            - <String>
                                            - ...
                                    )
                                trial_num:
                                    ...same as above.
                        )
                    trigger_name:
                        ...same as above.
            ) And/Or (
                triggers_list:
                    - <String>
                    - <String>
            )
    )

    Optional (
        eye1:
            ...same as above.
    )
dataset_name:
    ...same as above.


# Description

There can be any number of datasets specified with this. Each of them will be processed
with either just the default values (along with default pre-/post- prcoessing), or with more
specific values that are specified deeper within the structure. Those specifics start of
with either eye0 or eye1, then per trigger name, and finally per trial number in increasing time.

At each level, more and more specific functionality can be implemented, and other attributes
can be overwritten. For example, we can specify that some X, and Y triggers must be
segmented with different baseline and trial times, or use diffent pre and post processing
functions on specific trials. This could allow you to perhaps smooth data before it's resized,
or even resample it. This will also allow you to modify the data returned at each stage of the process.
The `*_pre_processing` and `*_post_processing` flags are used to deliver most of that functionality.

As the YAML conifig is parsed, the values that are defined at the previous level are
considered as defaults for the current level. For example, if the trial and baseline times
are defined at the trigger level, all of it's trials will use those settings, unless
otherwise specified in a trial number entry.


# Example

The best way to explain how to use this schema is through examples.

1) Specify multiple datatsets:

    -- Setting the times and triggers here, makes
    -- each dataset use them as the default.
    config:
        -- Maximum number of workers
        workers: 100
        -- Log to file
        logger: default

        -- Time after trigger marker
        trial_time: 2
        -- Time before the trigger marker
        baseline_time: -1
        triggers:
            - S11
            - S12
            - S13
            - S14
        -- This specifies that all trials in all datasets must run that additional processing function
        -- either before or after the trial is obtained, along with the default processing.
        trial_processing:
            - default  -- Always needs to be specified if you are modifying the default functions.
            - get_sums -- A function that will take the sum of the data values in the time series chunk.

    dataset1:
        dataset_path: C:\Recordings\CurrentStudy\001\block.xdf

    dataset2:
        dataset_path: C:\Recordings\CurrentStudy\002\block.xdf

    dataset3:
        dataset_path: C:\Recordings\CurrentStudy\003\block.xdf
