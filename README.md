
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1403896.svg)](https://doi.org/10.5281/zenodo.1403896)


# Pupil-Lib Python

This library is for processing data that is obtained from the Pupil Labs eye tracker working in conjunction with LSL that retrieves the event markers needed for this processing library. These event markers can be created anywhere i.e. a different computer and sent over network to the Lab Recorder. The XDF file's created can then be given to this library, with a configuration file (a YAML or .yml file), to perform trial-extraction.

Once processed by this library, the trials that are returned after extraction have zero error in their length relative to what was requested - leaving only small network latencies as the cause for errors. The data is also resampled into an evenly spaced timeseries to make processing and analysis simpler. This is particularly useful when we need to deal with un-evenly sampled data streams obtained from LSL's XDF data exports or the Pupil Labs eye tracker.

## Dependencies

For dependencies of this library (and past versions) see here: https://github.com/gmierz/pupil-lib#dependencies
Those tools are required when performing an experiment to collect the markers.

## Usage

Once you clone this library, you should run `python setup.py install` from within the directory so that you can use it in a script anywhere.

An easy way to get going after this is by just modifying `simple_script.py` to suit your needs, and changing `yaml_path='resources/test_yaml1.yml'` to point to another YAML file (which could be the same file - copied or not).

The markers that are recorded through LSL need to have the name 'Markers' as the name of the entry for the triggers. (There will soon be support for using any names).

One way is to use it is in a script with calls that resemble the `main()` function in pupil_lib.py. `yaml_path` must be defined
in the `get_build_config(yaml_path=<PATH/TO/YAML>)` call. Or if you don't need much control, `script_run(yaml_path=<PATH/TO/YAML>)`
in the same file can be used to do everything and return an PupilLibRunner object that contains the data in the field `.data_store`.

See `docs/data_container.md` for more information on the data container `.data_store` which holds all the data - `pupillib/simple_script.py` is a good example.

You can also use it through the command prompt as well with something like:
`python pupil_lib.py -D C:\Recordings\CurrentStudy\subj4\block__old41.xdf --data-names gaze_x gaze_y
 --trigger-pre-processing "{name: default}" {'name':'get_sums','config':[4]} -t S11 S12 --max-workers 1
 --tr -2 0 --logger stdout --test --testingdepth deep`

Or with only this to get the arguments from a YAML configuration file (defined in the docs/ folder):
`python pupil_lib.py --run-config C:\Users\Gregory\PycharmProjects\pupil_lib_parallel_exp\resources\test_yaml1.yml`

## Data Usage

`data_container.py` shows the general structure of the data once it's finished processing, with docs in `docs/data_container.md`. Generally speaking, accessing data will be similar in all cases to what is done in `simple_script.py`.

## Marker creation

Using the Pupil Labs LSL plugin, you can create and send markers from a stimulus script in the same way that is done here:
 https://github.com/sccn/labstreaminglayer/blob/master/LSL/liblsl-Python/examples/SendStringMarkers.py

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

This library, at it's core, only extracts trials. This is why it's main feature is zero-error trial extraction. But it uses processor files to perform any processing like percent-change calculations, and filtering. Because of this it is very simple to insert your own customized functionality before or after any part of the processing pipeline. See `pupillib/docs/pre_post_functions` for how to do this. In the near future, it will also be possible to add custom classes (extending from the processor classes) with the same decorators from a directory outside the library with an environment flag.

## Testing

Testing is done within the library itself, but it is only fully tested when `testing: True` is set in the `config` entry of a YAML configuration file. This makes it simpler to reproduce specific errors within a given dataset. There are also two test YAML files situated in `pupillib/resources`.

## Future Additions and Fixes

1. Custom class imports for processing.
2. Stronger/better CSV exporting.
3. Deprecation of all command line arguments except for `--run-config=<PATH>` for simplification purposes.
4. More documentation of data structures at the various pre/post processing levels.

## Academic Citation

There is no article to cite for this source code for the time being. However, if this code is used in any scientific publications, please consider referencing this repository with the following:

`
Mierzwinski,  W. G.  (2018).  Pupil-Lib  Data  Segmentation/Epoching/Trial-Extraction  Library  [Data set]. Github repository, https://github.com/gmierz/pupil-lib-python
`

You can personalize the link to a particular commit that you used in your processing. If a DOI is needed, you can ask for one through an issue and a Zenodo link will be provided. 

## License - GPLV3

Even though licensing of the python version of the library has not been completed for the moment, you can consider it as being licensed under GPLV3 just like the matlab version: https://github.com/gmierz/pupil-lib/blob/master/LICENSE

Finally, as always feel free to ask any questions you may have through issues and post your issues or suggested improvements through there as well. :)
