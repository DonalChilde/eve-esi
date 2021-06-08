# TODO

## before release

## rewrite to remove pfmsoft-aiohttp-queue dependency

- test aiohttp worker retry code.
  - make use of worker retry logic in EsiRemote.
    - remove retry logic from EsiRemote.
- update source code to use new AiohttpQueueRunner.
  - rethink success fail signals, re task exceptions.
- reorg source exceptions, include job.
- update EveEsiJob queue runners to AiohtpQueue format.
- make new observer for cli.
  - observers need to report job,exceptions
    - collect multiple exceptions from callbacks, make it so each callback has a chance to complete
    - use task exception reporting instead?
- wrap custom exceptions in callbacks
- eval moving/bridging job creation from operation_manifest to EveEsiJobs
- Update cli to use EveEsiJobs. pass that around instead of op_man
- Remove call_collection from tests
- Update cli tests.
- DONE Need a separate queue implementation for AiohttpRequests to get pages
  - change current code over to use new AiohttpRequest
  - simplify esiremote, remove duplicated function re AiohttpRequest and EsiSourceResult
    - rethink what im trying to accomplish here.
- fix pages - do pages have separate etags?
- implement local store
  - DONE Simplest solution is complete
- survey for logging
- fix cli
- update docs
- better messaging for observers
  - Make logging observer
- DONE move callbacks to eve-esi, adjust method sig.
  - callbacks work with jobs, not aiohttp.
- Jobs only have success callbacks.
  - DONE update model
- make remote and local providers.
  - app data store
    - data schema
    - route for non-direct esi data? eg. combined calls like region_id,name
      - static, derived, dynamic? some way to categorize, so that it is easy to regenerate selected parts of data store.
  - esi source
- make queue for jobs
- worker to run jobs queue
- def ensure_type(value,expected_type,custom_cast=None)->T:

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

## Project outline

### API

- Create jobs that can be saved to disk for reuse.
  - Serialize and deserialize from supported formats. Json, Yaml.
- Jobs offer optional callbacks for post processing.
  - Most likely used to save data to disk.
  - Callbacks should not change data stored on a job, make a copy as necessary.
- Do a list of jobs concurrently.
  - Put jobs in a queue.
  - Use a defined number of workers to do the jobs.
    - Workers support observer pattern for reporting on progress.
  - Retrieved data is stored in the job for later processing.
    - Also store retrieval state, and error messages.
    - Location of data used, local, remote
- Support local and remote data sources.
  - sources can be None, but one must exist
  - Local source is checked first for matching data.
    - Local source can be selectively purged/refreshed/expired.
    - Local source offers reports on age of data, size, etc.
  - Remote source is then checked to see if data is changed (Etag).
    - Remote source supports rate limiting, ops per second.
    - Remote source supports retrying for certain errors (500s).
  - Most recent data attatched to job, updated in local source as necessary.
