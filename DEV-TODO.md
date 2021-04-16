# TODO

## before release

- DONE CHANGE workorder.parent_path_template now workorder.output_path
- DONE ADD do job from cli without workorder
- ADD test for cli reporting failed jobs
  - needs jobs guaranteed to fail
    - bad url
    - bad kwarg to callback
    - missing param
    - too many params
- DONE FIX csv output does not respect file path templates.
- DONE CHANGE exclude default values during pydantic serialization
- DONE ADD add description to job model
- DONE ADD Multi job example workorder
  - DONE split output directories
  - DONE build jobs with various example callbacks
- DONE CHANGE sort model args for prettier yaml output
- DONE ADD cli success fail retry reporting
- DONE ADD async queue log level setting to env.
- DONE ADD create jobs can load custom callbacks from json file
  - DONE use default callbacks if not supplied
  - DONE alter tests to reflect new command
  - DONE add callback collection tests resources
- DONE ADD test function to generate test resources from examples
- DONE ADD create/add to workorders from cli
  - DONE tests
  - DONE fix output path
- DONE improve logging output and info.
- DONE CHANGE remove additional_attributes param from do_work_orders, add any additional attributes to respective workorder before processing.

- Docs
  - oh so many docs
  - reasonable cli help
- docs internal - write out program flow

## future releases

- compound functions for convenience.
  - region_ids with names
  - market groups
  - type_ids with names
  - type_ids in market
  - solarsystem info
  - rollup market lookup table
  - market history summary
- CHANGE path_in and out as Path not string, validate.
- ADD tests for adding jobs to existing workorder
- ADD tests for post jobs
- ADD validate jobs without running them - dry run
  - make the action but dont run it?
- ADD yaml input and output options.
  - callback to offer yaml output of data
  - DONE load and save yaml jobs and workorders
  - test on file path strings with spaces
  - rework tests to explicitly support both formats
  - detect format on load
- ADD callback that saves data with meta, to support local data store. maybe just a callback to save to the data store. Meh, implement this as a function on the data store?
  - subset of response meta
    - etag, date, op_id, params, cache expir?
    - enough to serve as cached data?
- custom exceptions?
- ADD switches for verbosity, support stdout, pipe to file
- ADD generate job methods from template
- ADD figure out auth
  - start with token in header? aquire manually and test function.

aiohttp-queue

- json save to file pass json kwargs
- yaml save to file pass yaml kwargs
