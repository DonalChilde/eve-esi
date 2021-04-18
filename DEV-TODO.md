# TODO

## before release

- Callback manifest redo

  - callback manifest default laods known callbacks, can add additional callbacks (user defined)
  - add_callback(callback_id,callback,factory_function, valid_targets)

- add yaml function to models, mixin?

- Docs
  - oh so many docs
  - reasonable cli help
- docs internal - write out program flow

## future releases

- test for cli reporting failed jobs

  - needs jobs guaranteed to fail
    - bad url
    - bad kwarg to callback
    - missing param
    - too many params

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
