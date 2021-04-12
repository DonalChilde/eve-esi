# TODO

## before release

- DONE - cli error reporting, success fail retry
  - test for output.
- DONE - load jsonfile of default callbacks - cli create job
  - DONE - use default callbacks if not supplied
  - alter tests to reflect new command
  - DONE add callback collection tests resources
- DONE test function to generate test resources from examples
- collect jobs to workorders
  - tests
  - change workorder string arg to a path to json file. Allows adding job to an existing work order.
  - DONE fix output path
- test post jobs
- make some jobs that will fail.
- improve logging output and info.
- validate jobs - create action?
- run job or workorder flag
- Docs
- docs internal - write out program flow

## future releases

- custom exceptions?
- generate job methods from template
- figure out auth
  - start with token in header? aquire manually and test function.

## sub projects

- Aiohttp Queue
  - str and repr for action
  - logging, retry and fail
- decide, add workorder attribute to job, or submit as additional_attributes
