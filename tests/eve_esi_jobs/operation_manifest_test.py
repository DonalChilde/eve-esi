from tests.eve_esi_jobs.conftest import FileResource

from eve_esi_jobs.operation_manifest import OperationInfo, OperationManifest


def test_schema_resource(esi_schema: FileResource):
    assert esi_schema.data["info"]["version"] == "1.7.15"


def test_esi_provider(operation_manifest):
    assert operation_manifest.version == "1.7.15"


# TODO tests for functions


# def test_build_path_parameters(operation_manifest: OperationManifest):
#     esi_job_json = {
#         "op_id": "get_markets_region_id_history",
#         "max_attempts": 1,
#         "parameters": {"region_id": 10000002, "type_id": 34},
#         "callbacks": {},
#     }
#     esi_job = models.EsiJob.deserialize_obj(esi_job_json)
#     jobs_to_actions = JobsToActions()
#     # pylint: disable=protected-access
#     path_params = jobs_to_actions._build_path_params(esi_job, esi_provider)
#     # print(path_params)
#     assert path_params["region_id"] == esi_job_json["parameters"]["region_id"]
#     assert len(list(path_params.keys())) == 1


# def test_build_query_parameters(esi_provider):
#     esi_job_json = {
#         "op_id": "get_markets_region_id_history",
#         "max_attempts": 1,
#         "parameters": {"region_id": 10000002, "type_id": 34},
#         "callbacks": {},
#     }
#     esi_job = models.EsiJob.deserialize_obj(esi_job_json)
#     jobs_to_actions = JobsToActions()
#     # pylint: disable=protected-access
#     query_params = jobs_to_actions._build_query_params(esi_job, esi_provider)
#     # print(query_params)
#     assert query_params["type_id"] == esi_job_json["parameters"]["type_id"]
#     assert len(list(query_params.keys())) == 1
