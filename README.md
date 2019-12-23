v1.2.0: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3474206.svg)](https://doi.org/10.5281/zenodo.3474206)
[![Build Status](https://travis-ci.com/gmierz/pupil-lib.svg?branch=master)](https://travis-ci.com/gmierz/pupil-lib)

# Pupil-Lib Python

This library is for processing data that is obtained from the [Pupil Labs](https://pupil-labs.com/) eye tracker working in conjunction with [Lab Streaming Layer](https://github.com/sccn/labstreaminglayer) (LSL) that retrieves the needed event markers and eye tracker data. These event markers can be created anywhere and sent over the network to the Lab Recorder. The XDF file's created can then be given to this library, with a configuration file [(a YAML or .yml file)](https://github.com/gmierz/pupil-lib-python/blob/master/pupillib/resources/test_yaml1.yml), to perform trial extraction. It can be used as a command line tool, or python module import.

Once processed by this library, the trials that are returned after extraction have zero error in their length relative to what was requested - leaving only small network latencies as the cause for errors. The data is also resampled into an evenly spaced timeseries to make processing and analysis simpler. This is particularly useful when we need to deal with un-evenly sampled data streams obtained from LSL's XDF data exports or the Pupil Labs eye tracker. These streams are also synchronized by LSL on import and have a [high level of precision](https://sccn.ucsd.edu/~mgrivich/LSL_Validation.html).

Another use of this library is the ability to convert Pupil Labs XDF files into CSV, or Matlab `.mat` files that can be processed anywhere. Data is also upsampled to 256Hz and corrected for irregular sampling rates. See [this file](https://github.com/gmierz/pupil-lib/blob/master/pupillib/example_xdf_to_csv.py) for an example.

The Matlab version is available here: https://github.com/gmierz/pupil-lib-matlab

This python version of the library will only work on Python 3+.

## Academic articles using this library

1. R. Butler, G.W. Mierzwinski, P.M. Bernier, M. Descoteaux, G. Gilbert, K. Whittingstall, __Neurophysiological basis of contrast dependent BOLD orientation tuning__, NeuroImage, 2019, 116323, ISSN 1053-8119, https://doi.org/10.1016/j.neuroimage.2019.116323.

## Recent Changes
The following changes are incorporated into the PyPi `pupillib` module at version 1.2.0.
1. Pupil LSL Relay 2.0 support.
2. Drastic increase in the number of time series that can be obtained. See this [sample config](https://github.com/gmierz/pupil-lib/blob/436c65301cd2323a06737dc6f1694f5664378fdf/pupillib/resources/test_yaml3.yml#L24).

The following changes are incorporated into the PyPi `pupillib` module at version 1.1.0.
1. Matlab '.mat' output is now supported! Instead of `save_csv`, use `save_mat` to store '.mat' files.
2. Merging multiple datasets is working as expected now.
3. Simplified rejected trial exclusion/inclusion from data. At any level of the data_container objects, set `datastore.exclude_rejects = False` to include rejected trials in the data obtained from `get_matrix` calls. Setting this flag to False also changes what is saved with the `save_csv` and `save_mat` functions since they use `get_matrix` to gather data that needs to be saved.
4. Raw trial data that is processed by some pre/post functions is no longer overwritten by the processed data. This data now exists in the `proc` data_type rather than the `original` data type.
5. Added --save-mat and --prefix to the optional arguments that can be used from the command line interface.
6. `.data` can now be used to access the processed data instead of `.data_store`. `.data_store` is still available but will be removed in a future release.
7. Documentation was updated to reflect the changes.
8. (Under-the-hood) Logging is now a bit simpler, and not as verbose as before. With this patch, preparations are being made to remove threaded options.

## Dependencies
To have an experiment compatible with this library the following is required:
  1. Pupil Labs binocular eye tracker: https://pupil-labs.com/ .
  2. Lab Streaming Library (LSL): https://github.com/sccn/labstreaminglayer . The version contained in 'liblsl-1.04.zip' in the downloads page is known to work with the Matlab marker inlet function.
      1. To install, you will have to clone the repo locally.
      1. For Matlab scripts, download the code in `LSL/liblsl-matlab` and `LSL/liblsl`.
      1. Copy the files in `liblsl` into `liblsl-matlab/bin`, then add the matlab directory into the matlab path.
      1. Now you can use it in a stimulus script.
  3. LabRecorder: ftp://sccn.ucsd.edu/pub/software/LSL/Apps/ . This version contained in 'LabRecorder-1.12c.zip' is known to work with the Pupil Labs eye tracker and produces compatible XDF files.
  4. Install [Pupil Labs LSL Plugin 2.0](https://github.com/labstreaminglayer/App-PupilLabs/tree/v2.0). Follow their instructions [in the readme](https://github.com/labstreaminglayer/App-PupilLabs/tree/v2.0). It should be possible to install `pylsl` with `pip install pylsl`.
  5. (Optional - Pupil Labs LSL Plugin 2.0 now works from step 4, if there are issues with that one then try this older version). Pupil Labs LSL Plugin: https://github.com/labstreaminglayer/App-PupilLabs/releases/tag/v1.0 . Follow [their instructions](https://github.com/labstreaminglayer/App-PupilLabs/tree/v1.0) to get it working. I had to use the source code in the Lab Streaming Library repo to be able to properly produce the 'pylsl' folder. What helped the most here was running the script 'get_deps.py' which will fill the 'pylsl' folder with needed files. This can be done before or after the 'build' phase. Ignore the link at "LSL Python bindings on the first step, it's broken and should point [here](https://github.com/labstreaminglayer/liblsl-Python/tree/v1.13.0) but it's not required.

## Running a compatible experiment

Any experiment must use the [Lab Recorder](https://github.com/labstreaminglayer/App-LabRecorder) to record all the data, the Pupil Labs LSL Relay Plugin (mentioned above) to send data from a Capture interface running on a network, and a Lab Streaming Layer outlet producing event markers (from any language) somewhere. See [here](https://github.com/gmierz/pupil-lib-matlab/blob/master/server_client/create_marker_outlet.m) for a Matlab example - use with `outlet.push_sample({'Marker Name'})` in a stimulus script. You can wait until it [has consumers](https://github.com/labstreaminglayer/liblsl-Matlab/blob/17c89909f8f28a1cdd96eef4a444432c4ace0753/lsl_outlet.m#L118) as well to automatically start stimuli from a Lab Recorder application.

Any experiment, in general, goes as follows:
1. Insert markers into stimulus scripts, and have it ready and waiting for consumers.
2. Start eye trackers, and Pupil Capture and prepare - ensure that the relay plugin is on.
3. Open Lab Recorder on a recording machine that is on to the same network the eye trackers and event markers are on.
4. Check boxes for all data required
    - `diameter_3d` (in mm) comes from the `Python representation`, and  `diameter` is the diameter (in pixels) uncorrected for perspective it is the only diameter available in the `Primitive data`.
    - Always remember to have the marker one selected, or the stimulus won't start if you're waiting on consumers.
    - If you're not sure what you need, take the python representation. It will result in large files, but it's also the only way to get perspective corrected diameters (or specific gaze data).
5. Start Lab Recorder when you're ready to start the experiment.

Note: There is no need to record from Pupil Capture, but you can if you still need to.

## Usage

Once you clone this library, you should run `python setup.py install` from within the directory so that you can use it in a script anywhere.
Here are some example commands:

```
cd ~
git clone https://github.com/gmierz/pupil-lib-python
cd pupil-lib-python
python setup.py install
```

You can also install this through pip now:
```
pip install pupillib
```

If any errors are encountered during installation, try using a virtual environment (these commands differ based on the OS - [see here for more info](https://virtualenv.pypa.io/en/latest/userguide/)):
```
pip install virtualenv

virtualenv pupillib-venv

pupillib-venv\Scripts\activate
pip install pupillib
```

After this, you will be able to use pupillib as a python module import or a command line tool with [YAML configurations](https://github.com/gmierz/pupil-lib-python/blob/master/pupillib/resources/test_yaml1.yml).

An easy way to get going after this is by using the script [pupillib/simple_script.py](https://github.com/gmierz/pupil-lib-python/blob/master/pupillib/simple_script.py) as an example to get what you need. Then change `yaml_path='resources/test_yaml1.yml'` to point to another YAML file (which could be the same file - copied or not) and modify the configuration to your experiment.

The markers that are recorded must have a type of 'Markers' to be processed. If the type is mixed with the name change `type` to `name` here:
One way is to use it is in a script with calls that resemble the `main()` function in pupil_lib.py. `yaml_path` must be defined
in the `get_build_config(yaml_path=<PATH/TO/YAML>)` call. Or if you don't need much control, `script_run(yaml_path=<PATH/TO/YAML>)`
in the same file can be used to do everything and return an PupilLibRunner object that contains the data in the field `.data_store`.

See `docs/data_container.md` for more information on the data container `.data_store` which holds all the data - `pupillib/simple_script.py` is a good example.

You can also use it through the command prompt as well with something like (this is the suggested method):

```
pupillib --run-config C:\Users\Gregory\PycharmProjects\pupil_lib_parallel_exp\resources\test_yaml1.yml`
```

Or with only this to get the arguments from a YAML configuration file (defined in the docs/ folder):

```
pupillib -D C:\Recordings\CurrentStudy\subj4\block__old41.xdf --data-names gaze_x gaze_y
 --trigger-pre-processing "{name: default}" {'name':'get_sums','config':[4]} -t S11 S12 --max-workers 1
 --tr -2 0 --logger stdout --test --testingdepth deep
```

## Data Usage

`data_container.py` shows the general structure of the data once it's finished processing, with docs in `docs/data_container.md`. Generally speaking, accessing data will be similar in all cases to what is done in `simple_script.py`.

## Marker creation

Using the Pupil Labs LSL plugin, you can create and send markers from a stimulus script in the same way that is [done here](https://github.com/labstreaminglayer/liblsl-Matlab/blob/17c89909f8f28a1cdd96eef4a444432c4ace0753/examples/SendStringMarkers.m).

The stream can/will be saved by the Lab Recorder software and that data can then be used for processing in this library.
(For the stimulus scripts, they can be in any language that LSL offers so that markers can be created and sent).

## Examples of data that can be retrieved

These images below are from processing a dataset where a subject was looking at these stimuli:

![alt text](https://user-images.githubusercontent.com/10966989/35007458-ce26d07a-fac7-11e7-9817-1e2c3f2bfc9e.png)

Gaze data (gaze_x, and gaze_y fields) - data from when a world camera was not in use:

![alt text](https://user-images.githubusercontent.com/10966989/35007537-f99df72e-fac7-11e7-9daa-d035ca92bd42.png)

All trials across all triggers:

![alt text](https://user-images.githubusercontent.com/10966989/35007535-f97cf86c-fac7-11e7-9eab-8949a9961a7e.png)

Mean of all trials for each trigger overlaid:

![alt text](https://user-images.githubusercontent.com/10966989/35007562-121dbcf8-fac8-11e7-9acd-c14bd579fdef.png)

## Customization

This library, at it's core, only extracts trials. This is why it's main features are zero-error trial extraction, and helping with the correction of uneven sampling rates. But it uses processor files to perform any processing like percent-change calculations, and filtering. Because of this it is very simple to insert your own customized functionality before or after any part of the processing pipeline. See `pupillib/docs/pre_post_functions` for how to do this. In the near future, it will also be possible to add custom classes (extending from the processor classes) with the same decorators from a directory outside the library with an environment flag.

## Testing

Testing is done within the library itself, but it is only fully tested when `testing: True` is set in the `config` entry of a YAML configuration file. This makes it simpler to reproduce specific errors within a given dataset. There are also two test YAML files situated in `pupillib/resources`.

## Future Additions and Fixes

1. Custom class imports for processing.
2. Stronger/better CSV exporting.
3. Deprecation of all command line arguments except for `--run-config=<PATH>` for simplification purposes.
4. More documentation of data structures at the various pre/post processing levels.

## Academic Citation

There is no article to cite for this source code for the time being. However, if this code is used in any scientific publications, please consider referencing this repository by following the Zenodo badge link, and using the "cite as" entry from there:

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.2589448.svg)](https://doi.org/10.5281/zenodo.2589448)

If you need a newer release, you can let me know through an issue.

## License - GPLV3
This library is licensed under GPLV3, see here for the license: https://github.com/gmierz/pupil-lib/blob/master/LICENSE
If another type is required please contact me so that we can discuss.

Finally, as always feel free to ask any questions you may have through issues and post your issues or suggested improvements through there as well. :)
