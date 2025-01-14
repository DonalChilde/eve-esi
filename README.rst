============
Eve Esi Jobs
============


.. image:: https://img.shields.io/pypi/v/eve_esi_jobs.svg
        :target: https://pypi.python.org/pypi/eve_esi_jobs

.. image:: https://img.shields.io/travis/DonalChilde/eve_esi_jobs.svg
        :target: https://travis-ci.com/DonalChilde/eve_esi_jobs

.. image:: https://readthedocs.org/projects/eve-esi-jobs/badge/?version=latest
        :target: https://eve-esi-jobs.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status



An api and command line utility for asyncronous interaction with Eve Online's Esi api.


* Free software: MIT license
* Documentation: https://eve-esi.readthedocs.io.


Features
--------

* Async calls to Eve Online's `Eve Swagger Interface`_.
* repeatable cli actions based on json command files.
* api for easy creation of commands, use it as a layer in your own programs.
* Templated file paths to get your data just where you want it.
* Command line completion with Typer_.
* Csv or json output of downloaded data.
* Generate jobs from csv input.
* Handles resulting data via async callbacks.
* Json or yaml input and output of workorder and job files.

Up Coming Features
------------------

* Yaml callback for downloaded data.
* custom file path template values from the command line.
* Even more options for Templated file output.
* Pre-made commands for easy download of static data.
* Generate a summary of market history, with a customizable date range
* Generate a current lookup csv of the most commonly used info, eg. type_id, name, market_group, meta_level
* Handle oath2 registration for restricted apis

Warnings
--------

* This program works, but it is early days. It still needs lots of:
        *   Error handling
        *   Documentation
        *   Testing
        *   general refinement
* The api may change as things evolve.

eve-esi cli
-----------

quickstart
..........

First, get a current copy of the ESI schema.json:

.. code-block:: console

        $ eve-esi schema download

You will see a message detailing where the schema was saved to. This will be a system specific folder for app data determined by Click.


Now use the command line app to generate some example work orders:

.. code-block:: console

        $ eve-esi examples all-examples

.. note::

  The default output directory is ./tmp

You should see something like this:

.. code-block:: console

  ./tmp
  └── examples
      ├── callbacks
      │   ├── generic_save_result_and_job_to_same_json.json
      │   ├── generic_save_result_and_job_to_same_json.yaml
      │   ├── generic_save_result_and_job_to_separate_json.json
      │   ├── generic_save_result_and_job_to_separate_json.yaml
      │   ├── generic_save_result_to_json.json
      │   ├── generic_save_result_to_json.yaml
      │   ├── no_file_output.json
      │   └── no_file_output.yaml
      ├── input-data
      │   ├── market_history_params.csv
      │   ├── market_history_params_extras.csv
      │   ├── market_history_params_extras.json
      │   ├── market_history_params_extras.yaml
      │   ├── market_history_params.json
      │   ├── market_history_params.yaml
      │   ├── region_ids.csv
      │   ├── region_ids.json
      │   ├── region_ids.yaml
      │   ├── type_ids.csv
      │   ├── type_ids.json
      │   └── type_ids.yaml
      ├── jobs
      │   ├── get_industry_facilities.json
      │   ├── get_industry_facilities.yaml
      │   ├── get_industry_systems.json
      │   ├── get_industry_systems.yaml
      │   ├── post_universe_names.json
      │   └── post_universe_names.yaml
      └── workorders
          ├── example_workorder.json
          ├── example_workorder.yaml
          ├── response_to_job_json_file.json
          ├── response_to_job_json_file.yaml
          ├── result_and_response_to_job_json_file.json
          ├── result_and_response_to_job_json_file.yaml
          ├── result_to_csv_file.json
          ├── result_to_csv_file.yaml
          ├── result_to_job_json_file.json
          ├── result_to_job_json_file.yaml
          ├── result_to_json_file_and_response_to_json_file.json
          ├── result_to_json_file_and_response_to_json_file.yaml
          ├── result_to_json_file.json
          ├── result_to_json_file.yaml
          ├── result_with_pages_to_json_file.json
          └── result_with_pages_to_json_file.yaml


* jobs - Retrieve a resource from the Eve ESI and manipulate it.
* callbacks - Sets of pre-defined actions that can be applied to a job.
* workorders - A collection of jobs that can run concurrently, greatly reducing the time spent.
* input-data - Examples of file data that can be used to quickly create jobs.

Notice that workorders, jobs, and callbacks come in both json and yaml versions. Both formats are supported.


.. todo::

  * link to model specification
  * link to callback descriptions.


Run a work order,

.. code-block:: console

        $ eve-esi do workorder ./tmp/examples/work-orders/result_to_json_file.json  ./tmp

and the resulting (output abreviated) folder should look like:

.. code-block:: console

  ./tmp
  └── examples
      ├── order_output
      │   └── result_to_json_file
      │       └── data
      │           └── market-history
      │               └── 10000002-34.json


with the resulting (abreviated) file `10000002-34.json` looking like:

.. code-block:: json

        [
          {
            "average": 7.73,
            "date": "2020-03-01",
            "highest": 8.0,
            "lowest": 7.66,
            "order_count": 2775,
            "volume": 9085235901
          },
          {
            "average": 7.97,
            "date": "2020-03-02",
            "highest": 8.1,
            "lowest": 7.57,
            "order_count": 2301,
            "volume": 7957717372
          },
          {
            "average": 7.94,
            "date": "2020-03-03",
            "highest": 8.19,
            "lowest": 7.71,
            "order_count": 1979,
            "volume": 5789013369
          },
        ]


Try out the different examples to see the possible outputs.

.. todo::

  See -link to future api doc- for a list of available values for use in file paths.

eve-esi schema
..............

.. todo::

  examples of:

  * Download the schema
  * list the possible operations
  * browse more indepth information on a particular operation

eve-esi create
..............

.. todo::

  examples of:

  * create jobs
  * create workorders



eve-esi do
..........

.. todo::

  examples of:

  * do jobs
  * do workorders

Credits
-------

This package was created with Cookiecutter_ and the `donalchilde/cookiecutter-pypackage-click`_ project template, derived from the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _`Eve Swagger Interface`: https://esi.evetech.net/ui/
.. _`donalchilde/cookiecutter-pypackage-click`: https://github.com/donalchilde/cookiecutter-pypackage-click
.. _`Typer`: https://typer.tiangolo.com/
