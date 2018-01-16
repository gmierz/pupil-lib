# Pupil-Lib Python

# Usage

Either use it in a script with calls that resemble the `main()` function in pupil_lib.py. `yaml_path` must be defined
in the `get_build_config(yaml_path=<PATH/TO/YAML>)` call.

You can use it through the command prompt as well with something like:
`python pupil_lib.py -D C:\Recordings\CurrentStudy\subj4\block__old41.xdf --data-names gaze_x gaze_y
 --trigger-pre-processing "{name: default}" {'name':'get_sums','config':[4]} -t S11 S12 --max-workers 1
 --tr -2 0 --logger stdout --test --testingdepth deep
 --run-config C:\Users\Gregory\PycharmProjects\pupil_lib_parallel_exp\resources\test_yaml1.yml`

Or with only this to get the arguments from a YAML configuration file (defined in the docs/ folder):
`python pupil_lib.py --run-config C:\Users\Gregory\PycharmProjects\pupil_lib_parallel_exp\resources\test_yaml1.yml`

# Data Usage

data_container.py shows the general structure of the data once it's finished processing. Generally speaking, accessing data
will be similar in all cases to what is done in `main()` in pupil_lib.py.