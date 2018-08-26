# Pre and Post Processing Functions

This library allows the user to insert pre and post processing functions at any level in the pipeline. That is, before and after all datasets, data streams, triggers, and trials. All functions added in the files in `pupillib/core/workers/processors/` should be decorated with `@pre` if the function should be run before the trial extraction process, or `@post` for after the trial extraction process.

They also need to always take two arguments: `*_data`, and `config` with * being the level (see code for examples). The config argument allows you to store and retrieve anything you'd like through the YAML config.

This allows you to use custom filtering (and other things like that) within the library without needing to add it all to a script later - letting you write it once and easily reuse it later.

The biggest point to remember is that you should never actually remove the trials at any stage - only mark them with the 'reject' flag set to true. This will help later when viewing the data so that you can still look at the rejected trials by using `get_all_trials_matrix` on a PupilTrigger object. A good example to look at would be `pupillib/core/workers/processors/trigger_processor.py`.