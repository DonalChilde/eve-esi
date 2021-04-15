# TODO

## before release

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
- CHANGE remove additional_attributes param from do job and do work_orders.
  - add any additional attributes to respective workorder or job before processing.
- ADD repr for models?

- Docs
  - oh so many docs
- docs internal - write out program flow

## future releases

- ADD tests for adding jobs to existing workorder
- ADD tests for post jobs
- ADD validate jobs without running them - dry run
  - make the action but dont run it?
- ADD run job from cli without workorder
  - make this separate commands
- ADD test for cli reporting failed jobs
  - needs jobs guaranteed to fail
- yaml input and output options.
  - callback to offer yaml output of data
  - load and save yaml jobs and workorders
  - test on file path strings with spaces
  - rework tests to explicitly support both formats
  - detect format on load
- callback that saves data with meta
  - subset of response meta
    - etag, date, op_id, params, cache expir?
    - enough to serve as cached data?
- custom exceptions?
- switches for verbosity, support stdout, pipe to file
- generate job methods from template
- figure out auth
  - start with token in header? aquire manually and test function.
