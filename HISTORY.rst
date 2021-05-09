=======
History
=======

0.1.3 (2021-05-09)
------------------

* ADD yaml file output example
* CHANGE Update to Pfmsoft Aiohttp Queue 0.2.1
* CHANGE translating job to AiohttpActions now done in JobsToActions
* ADD Option for yaml input and output of jobs and workorders.
* CHANGE workorder.parent_path_template now workorder.output_path
* ADD do job from cli without workorder
* ADD support for action observer,cli registers observer to report on failed actions.
* ADD cli reports failure details
* CHANGE retry_limit to max_attempts, matches underlying Action
* FIX csv output does not respect file path templates.
* CHANGE exclude default values during pydantic serialization
* ADD add description to job model
* ADD Multi job example workorder
* CHANGE sort model args for prettier yaml output
* ADD cli success fail retry reporting
* ADD async queue log level setting to env.
* ADD create jobs can load custom callbacks from json file, use default callbacks if not supplied
* ADD test function to generate test resources from examples
* ADD create/add to workorders from cli
* ADD improve logging output and info.
* CHANGE remove additional_attributes param from do_work_orders, add any additional attributes to respective workorder before processing.

0.1.2 (2021-04-00)
------------------

* Added Schema Browse command to cli, browse by op_id with completions! Get operation info used to build jobs.
* Added Schema List to cli, get a list of all op_ids, output to stdout, with a json format option.
* Added CSV output to available callbacks.
* Added Create command to cli. Create one or more jobs from a combination of command line and file input.

0.1.1 (2021-03-20)
------------------

* First release on PyPI.
