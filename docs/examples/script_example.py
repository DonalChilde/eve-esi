#!/usr/bin/env python

import json
import urllib.request
from pathlib import Path

from eve_esi_jobs import OperationManifest, do_workorder, models
from eve_esi_jobs.model_helpers import default_callback_collection


def example():
    # If the ESI schema does not exist locally, download and save it.
    PATH_TO_SCHEMA: Path = Path.home() / Path("tmp/esi-schema.json")
    if PATH_TO_SCHEMA.is_file():
        schema = PATH_TO_SCHEMA.read_text()
    else:
        URL = "https://esi.evetech.net/latest/swagger.json"
        with urllib.request.urlopen(URL) as response:
            schema_bytes = response.read()
            PATH_TO_SCHEMA.parent.mkdir(parents=True, exist_ok=True)
            PATH_TO_SCHEMA.write_bytes(schema_bytes)
            print(f"Downloaded schema from {URL}")
            schema = PATH_TO_SCHEMA.read_text()
            print(f"Schema saved to {PATH_TO_SCHEMA}")

    schema_json = json.loads(schema)
    operation_manifest = OperationManifest(schema_json)

    workorder = models.EsiWorkOrder()
    workorder.name = "Script-Example"
    workorder.id_ = "script_example"
    # not used for this example, as the default_callback_collection()
    # has no file output callbacks.
    workorder.output_path = "${ewo_name}/output/"

    job_1 = models.EsiJob(op_id="get_markets_region_id_history")
    job_1.name = "First-Job"
    job_1.parameters = {"region_id": 10000002, "type_id": 34}
    job_1.callbacks = default_callback_collection()
    workorder.jobs.append(job_1)

    job_2 = models.EsiJob(op_id="get_markets_region_id_history")
    job_2.name = "Second-Job"
    job_2.parameters = {"region_id": 10000002, "type_id": 36}
    job_2.callbacks = default_callback_collection()
    workorder.jobs.append(job_2)

    do_workorder(workorder, operation_manifest)

    print(workorder.name)
    for job in workorder.jobs:
        print(job.name)
        print(job.result.data[:3])


if __name__ == "__main__":
    example()
