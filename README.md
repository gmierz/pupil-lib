# Pupil-Lib Python

This library is for processing data that is obtained from the Pupil Labs eye tracker working in conjunction with LSL
that retrieves the event markers needed for this processing library. These event markers can be created anywhere i.e.
a different computer and sent over network to the Lab Recorder.

## Usage

Once you clone this library, you should run `python setup.py install` from within the directory so that you can use it in a script anywhere.

The markers that are recorded through LSL need to have the name 'Markers' as the name of the entry for the triggers. (There will soon be support for using any names).

One way is to use it is in a script with calls that resemble the `main()` function in pupil_lib.py. `yaml_path` must be defined
in the `get_build_config(yaml_path=<PATH/TO/YAML>)` call. Or if you don't need much control, `script_run(yaml_path=<PATH/TO/YAML>)`
in the same file can be used to do everything and return an PupilLibRunner object that contains the data in the field `.data_store`.

See `docs/data_container.md` for more information on the data container `.data_store`.

You can also use it through the command prompt as well with something like:
`python pupil_lib.py -D C:\Recordings\CurrentStudy\subj4\block__old41.xdf --data-names gaze_x gaze_y
 --trigger-pre-processing "{name: default}" {'name':'get_sums','config':[4]} -t S11 S12 --max-workers 1
 --tr -2 0 --logger stdout --test --testingdepth deep`

Or with only this to get the arguments from a YAML configuration file (defined in the docs/ folder):
`python pupil_lib.py --run-config C:\Users\Gregory\PycharmProjects\pupil_lib_parallel_exp\resources\test_yaml1.yml`

## Data Usage

`data_container.py` shows the general structure of the data once it's finished processing, with docs in `docs/data_container.md`. Generally speaking, accessing data
will be similar in all cases to what is done in `simple_script.py`.

## Marker creation

Using the Pupil Labs LSL plugin, you can create and send markers from a stimulus script in the same way that is done here:
 https://github.com/sccn/labstreaminglayer/blob/master/LSL/liblsl-Python/examples/SendStringMarkers.py

The stream can/will be saved by the Lab Recorder software and that data can then be used for processing in this library.
(For the stimulus scripts, they can be in any language that LSL offers so that markers can be created and sent).

## Examples of data that can be retrieved

These images below are from processing a dataset where a subject was looking at these stimuli:

![alt text](https://user-images.githubusercontent.com/10966989/35007458-ce26d07a-fac7-11e7-9817-1e2c3f2bfc9e.png)

Gaze data (gaze_x, and gaze_y fields):

![alt text](https://user-images.githubusercontent.com/10966989/35007537-f99df72e-fac7-11e7-9daa-d035ca92bd42.png)

All trials across all triggers:

![alt text](https://user-images.githubusercontent.com/10966989/35007535-f97cf86c-fac7-11e7-9eab-8949a9961a7e.png)

Mean of all trials for each trigger overlaid:

![alt text](https://user-images.githubusercontent.com/10966989/35007562-121dbcf8-fac8-11e7-9acd-c14bd579fdef.png)
