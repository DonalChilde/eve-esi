import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from rich import print

from eve_esi_jobs.exceptions import BadOpId, BadRequestParameter, MissingParameter
from eve_esi_jobs.helpers import combine_dictionaries, optional_object
from eve_esi_jobs.models import EsiJob, JobCallback

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class ParametersByLocation:
    body: Dict[str, Any] = field(default_factory=dict)
    query: Dict[str, Any] = field(default_factory=dict)
    path: Dict[str, Any] = field(default_factory=dict)
    header: Dict[str, Any] = field(default_factory=dict)

    def consolidate_params(self):
        combined = {}
        return combine_dictionaries(
            combined, [self.body, self.query, self.path, self.header]
        )


@dataclass
class OperationInfo:
    op_id: str
    method: str
    description: str
    path: str
    parameters_by_location: ParametersByLocation
    required_params: List[str]
    responses: Dict[str, Any]

    def request_params_to_locations(self, params: Dict) -> ParametersByLocation:
        """Split request parameters into their locations.

        Note: extra parameters are not used.
        """
        request_params_by_location = ParametersByLocation()
        for key, value in params.items():
            if key in self.parameters_by_location.body:
                request_params_by_location.body[key] = value
            elif key in self.parameters_by_location.query:
                request_params_by_location.query[key] = value
            elif key in self.parameters_by_location.path:
                request_params_by_location.path[key] = value
            elif key in self.parameters_by_location.header:
                request_params_by_location.header[key] = value
        return request_params_by_location

    def check_params(self, request_params: Dict):
        request_set = set(request_params.keys())
        if not set(self.required_params).issubset(request_params):
            raise MissingParameter(
                f"Missing required parameters for {self.op_id}, expected "
                f"{self.required_params} was given {request_set}"
            )
        for key, value in request_params.items():
            if value == "NOTSET":
                raise BadRequestParameter(f"Required parameter {key} is 'NOTSET'")

    def build_default_params(
        self,
        only_required: bool = False,
    ):
        params = {}
        for key, value in self.parameters_by_location.consolidate_params().items():
            if only_required:
                if value.get("required", False):
                    params[key] = value.get("default", "NOTSET")
            else:
                if value.get("required", False) or "default" in value:
                    params[key] = value.get("default", "NOTSET")
        return params

    def create_job(
        self,
        parameters: Dict,
        callbacks: Optional[List[JobCallback]] = None,
        include_default_params: bool = False,
    ) -> EsiJob:
        # FIXME is this used?
        if include_default_params:
            default_params = self.build_default_params()
            combined_params = combine_dictionaries(default_params, [parameters])
        else:
            combined_params = parameters
        callbacks = optional_object(callbacks, list)
        filtered_params_by_location = self.request_params_to_locations(combined_params)
        job_params = filtered_params_by_location.consolidate_params()
        job_dict = {
            "op_id": self.op_id,
            "name": "",
            "parameters": job_params,
            "callbacks": callbacks,
        }
        job = EsiJob.deserialize_obj(job_dict)

        return job


class OperationManifest:
    def __init__(self, schema: Dict) -> None:
        self.version = schema["info"]["version"]
        self.host: str = schema["host"]
        self.base_path: str = schema["basePath"]
        self.common_parameters: Dict[str, Any] = self._common_params(schema)
        self.manifest: Dict[str, OperationInfo] = self._parse_op_infos(schema)

    def _parse_op_infos(self, schema):
        manifest = {}
        for path, path_schema in schema["paths"].items():
            for method, method_schema in path_schema.items():
                dereferenced_parameters = self._deref_params(
                    method_schema["parameters"]
                )
                op_info = OperationInfo(
                    op_id=method_schema["operationId"],
                    method=method,
                    description=method_schema["description"],
                    path=path,
                    parameters_by_location=self._params_by_location(
                        dereferenced_parameters
                    ),
                    required_params=self._required_params(dereferenced_parameters),
                    responses=method_schema["responses"],
                )
                manifest[op_info.op_id] = op_info
        return manifest

    def available_op_ids(self) -> List[str]:
        return list(self.manifest.keys())

    def op_info(self, op_id: str) -> OperationInfo:
        op_info = self.manifest.get(op_id, None)
        if op_info is None:
            raise BadOpId(f"Could not find op_id: {op_id} in manifest.")
        return op_info

    def url_template(self, op_id: str) -> str:
        op_info = self.manifest[op_id]
        path_template = op_info.path.replace("{", "${")
        url_template = "https://" + self.host + self.base_path + path_template
        return url_template

    def _common_params(self, schema: Dict) -> Dict[str, Any]:
        common_params: Dict[str, Any] = schema["parameters"]
        return common_params

    def _required_params(self, parameters: List[Dict]) -> List[str]:
        required_params = []
        for param in parameters:
            if param.get("required", False):
                required_params.append(param.get("name", None))
        return required_params

    def _params_by_location(self, parameters: List[Dict]) -> ParametersByLocation:
        by_location = ParametersByLocation()
        param_list: List[Dict] = self._deref_params(parameters)
        # print(param_list)
        for param in param_list:

            try:
                if param["in"] == "body":
                    by_location.body[param["name"]] = param
                elif param["in"] == "query":
                    by_location.query[param["name"]] = param
                elif param["in"] == "path":
                    by_location.path[param["name"]] = param
                elif param["in"] == "header":
                    by_location.header[param["name"]] = param
                else:
                    raise ValueError(
                        f"Unexpected location value in {param} expected one "
                        f"of {['body','query','path','header']}"
                    )
            except Exception as ex:
                print(param_list)
                logger.exception("Param: %s List: %s", param, param_list)
                raise ex
            # print(param)
            # for key, value in param.items():
            #     try:
            #         if value["in"] == "body":
            #             by_location.body[key] = value
            #         elif value["in"] == "query":
            #             by_location.query[key] = value
            #         elif value["in"] == "path":
            #             by_location.path[key] = value
            #         elif value["in"] == "header":
            #             by_location.header[key] = value
            #         else:
            #             raise ValueError(
            #                 f"Unexpected location value in {value} expected one "
            #                 f"of {['body','query','path','header']}"
            #             )
            #     except Exception as ex:
            #         print(param_list)
            #         logger.exception("Param: %s List: %s", param, param_list)
            #         raise ex
        return by_location

    def _deref_params(self, parameters: List[Dict[str, Dict]]) -> List[Dict]:
        """de reference the common params from self.common_parameters"""
        param_list: List[Dict] = []
        for param in parameters:
            if "$ref" in param:
                split_value = param["$ref"].split(sep="/")  # type: ignore
                param_id = split_value[-1]
                param_list.append(self.common_parameters[param_id])
            else:
                param_list.append(param)
        return param_list
