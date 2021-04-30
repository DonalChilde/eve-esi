# TODO

## before release

- DONE ADD yaml file output example
- DONE move build action to job to action from esi_provider
- ADD organize testing, offer fixtures for some EsiJobs, and EsiWorkOrders?
  - maybe just work from current test_resources
  - look through older examples, make sure they are clear.
- One place for pre defined callback collections?
- DONE EsiProvider rethink
  - op_id info rethink
    - split parameters by location
    - add function to return required parameters
- DONE AiohttpQueue v0.2.0 release fixes
  - update callbacks
    - repr
    - file_path_template
- DONE Callback manifest redo
  - callback manifest default loads known callbacks, can add additional callbacks (user defined)
  - add_callback(callback_id,callback,factory_function, valid_targets)
- DONE add yaml function to models, mixin?

- Docs
  - oh so many docs
  - reasonable cli help
- docs internal - write out program flow

## future releases

- ADD JobCallback builder to CallbackManifest
  - so we get a runtime error for missing callback_id during api construction.
  - offer validation, at least as far as creating a callback, and seeing if args are there.
    - use existing init_callback.
- ADD default useragent header
- ADD cli option to add custom path values.
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
