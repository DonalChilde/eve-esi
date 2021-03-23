from asyncio.queues import Queue
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from aiohttp import ClientSession

from eve_esi.app_config import SCHEMA_URL, logger
from eve_esi.pfmsoft.util.async_actions.aiohttp import (
    AiohttpAction,
    AiohttpActionCallback,
    AiohttpActionMessenger,
    LogFail,
    LogRetry,
    LogSuccess,
    ResponseToJson,
)
from eve_esi.pfmsoft.util.collection.misc import optional_object

DEFAULT_CALLBACKS: Dict[str, Sequence[AiohttpActionCallback]] = {
    "success": [ResponseToJson(), LogSuccess()],
    "retry": [LogRetry()],
    "fail": [LogFail()],
}


def get_schema():
    action: AiohttpAction = AiohttpAction(
        method="get",
        url_template=SCHEMA_URL,
        action_callbacks=DEFAULT_CALLBACKS,
    )
    return action


@dataclass
class Op_IdLookup:
    method: str
    path: str
    path_template: str
    parameters: Dict = field(default_factory=dict)


class EsiProvider:
    """
    # TODO param validation
    # TODO default callbacks


    [extended_summary]
    """

    def __init__(self, schema):
        self.schema = schema
        self.op_id_lookup: Dict[str, Op_IdLookup] = self.make_op_id_lookup(self.schema)
        for op_id in self.op_id_lookup:
            self.op_id_lookup[op_id].parameters = self.make_op_id_params(op_id)

    def schema_version(self) -> str:
        return self.schema["info"]["version"]

    def make_op_id_lookup(self, schema) -> Dict[str, Op_IdLookup]:
        lookup = {}
        for path, path_schema in schema["paths"].items():
            for method, method_schema in path_schema.items():
                op_id = method_schema["operationId"]
                lookup[op_id] = Op_IdLookup(
                    method=method,
                    path=path,
                    path_template=self.make_path_template(path),
                    parameters={},
                )
        return lookup

    def make_op_id_params(
        self,
        op_id: str,
    ) -> Dict:
        # params_example = {
        #     "parameters": {"param_name": {"attribute_name": "attribute value"}}
        # }

        op_id_params: Dict = {}
        for param in self.operation_parameters(op_id):
            ref_check = param.get("$ref", None)
            if ref_check is None:
                op_id_params[param["name"]] = param
            else:
                common_param = self.resolve_common_parameter(ref_check)
                op_id_params[common_param["name"]] = common_param
        return op_id_params

    def resolve_common_parameter(
        self,
        ref_value: str,
    ):
        split_ref_value = ref_value.split(sep="/")
        param_id = split_ref_value[-1]
        common_parameters = self.common_parameters()
        params = common_parameters.get(param_id, None)
        if params is None:
            raise ValueError(f"Ref value {ref_value} not found in common parameters.")
        return params

    def common_parameters(self) -> Dict:
        return self.schema["parameters"]

    def operation_parameters(self, op_id) -> List[Dict]:
        path = self.op_id_lookup[op_id].path
        method = self.op_id_lookup[op_id].method
        parameters = self.schema["paths"][path][method]["parameters"]
        return parameters

    def make_path_template(self, path: str) -> str:
        return path.replace("{", "${")

    def lookup_url_template(self, op_id) -> Tuple[str, str]:
        data = self.op_id_lookup.get(op_id, None)
        if data is None:
            raise NotImplementedError(f"missing data for {op_id}")
        method = data.method
        # TODO handle route version changes
        url_template = (
            "https://"
            + self.schema["host"]
            + self.schema["basePath"]
            + data.path_template
        )
        return (method, url_template)

    def validate_params(self, op_id, path_params, query_params) -> bool:
        return True

    def build_action(
        self,
        op_id: str,
        path_params,
        query_params,
        action_callbacks: Optional[Dict[str, Sequence[AiohttpActionCallback]]] = None,
        action_messengers: Optional[Sequence[AiohttpActionMessenger]] = None,
        retry_limit=5,
        request_kwargs: Optional[dict] = None,
        context: Optional[Dict] = None,
    ) -> AiohttpAction:
        method, url_template = self.lookup_url_template(op_id)
        if not self.validate_params(op_id, path_params, query_params):
            raise NotImplementedError(
                "Error validating params, this should be move to validation function."
            )
        request_kwargs = optional_object(request_kwargs, dict)
        request_kwargs["params"] = query_params
        action = AiohttpAction(
            method,
            url_template,
            url_parameters=path_params,
            retry_limit=retry_limit,
            request_kwargs=request_kwargs,
            action_callbacks=action_callbacks,
            action_messengers=action_messengers,
            context=context,
        )
        return action


# def validate_params(esi_provider: EsiProvider, op_id, params) -> Dict:
#     path_params = validate_path_params(esi_provider, op_id, params)
#     query_params = validate_query_params(esi_provider, op_id, params)
#     return {"path_params": path_params, "query_params": query_params}


# def validate_path_params(esi_provider: EsiProvider, op_id, params) ->List[Dict}:
#     path_parameters = {}
#     # common_parameters = esi_provider.common_parameters()
#     # operation_parameters = esi_provider.operation_parameters(op_id)
#     # # TODO make a store of consolidated parameters on esi_provider to avoid repetition
#     # TODO combine commom and operational params
#     # check that all required params are present, return path_params
#     # add default params

#     return


def validate_query_params(esi_provider: EsiProvider, op_id, params) -> Dict:
    return {}

    """
    command to output a sample csv file that contains fields for a download operation.
    ability to chain command files together for quicker download times
    json file to have more command options?
    some options only on first line of csv.


    """
