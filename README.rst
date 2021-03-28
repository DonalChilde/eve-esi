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



A command line utility for interacting with Eve Online's Esi api.


* Free software: MIT license
* Documentation: https://eve-esi.readthedocs.io.


Features
--------

* Async calls to Eve Online's `Eve Swagger Interface`_
* repeatable cli access based on json command files.
* api for easy creation of commands, use it a layer in your own programs.
* Templated file paths to get your data just where you want it.

Up Coming Features
------------------

* Command line completion with Typer_
* csv output with added custom fields
* generating jobs from csv input
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
        *   A pluggable callback function
        *   general refinement
* The api may change as things evolve.

Usage
-----

First, get a current copy of the ESI schema.json:

.. code-block:: console

        $ eve-esi schema get

You may see some error messages the first time, then you will see a message detailing where the schema was saved to. This will be a system specific folder for app data determined by Click.


Now use the command line app to generate some example work orders:

.. code-block:: console

        $ eve-esi jobs work-order-samples ./tmp

You should see something like this:

.. code-block:: console

        /home/chad/projects/eve/eve_esi/tmp/
        └── samples
            ├── response_to_job.json
            ├── result_and_response_to_job.json
            ├── result_to_file_and_response_to_job.json
            ├── result_to_file.json
            └── result_to_job.json

Each of these files represents a work order that can retrieve one or more resources from the ESI.
Run a work order like this:

.. code-block:: console

        $ eve-esi jobs run ./tmp/samples/result_to_file.json ./tmp

and the resulting folder should look like:

.. code-block:: console

        /home/chad/projects/eve/eve_esi/tmp/
        └── samples
            ├── order_output
            │   └── result_to_file
            │       └── data
            │           └── market-history
            │               └── 10000002-34.json
            ├── response_to_job.json
            ├── result_and_response_to_job.json
            ├── result_to_file_and_response_to_job.json
            ├── result_to_file.json
            └── result_to_job.json

Try out the different examples to see the possible outputs.

There are a number of values that can be used in the file paths, and if you are using the api you can make your own.

A workorder :py:class:`eve_esi_jobs.models.EsiWorkOrder` will contain one or more jobs :py:class:`eve_esi_jobs.models.EsiJob`, a parent path fragment for its jobs, and a dict of key:value pairs that are used in Templates. TODO - explain override hierarchy.

see :py:mod:`eve_esi_jobs.sample_work_orders` for examples of making the work orders programaticaly, and :py:func:`eve_esi_jobs.eve_esi_jobs.do_work_order` for the function that gets work done.

Credits
-------

This package was created with Cookiecutter_ and the `donalchilde/cookiecutter-pypackage-click`_ project template, derived from the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _`Eve Swagger Interface`: https://esi.evetech.net/ui/
.. _`donalchilde/cookiecutter-pypackage-click`: https://github.com/donalchilde/cookiecutter-pypackage-click
.. _`Typer`: https://typer.tiangolo.com/
