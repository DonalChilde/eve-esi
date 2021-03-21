from asyncio.queues import Queue
from typing import Dict, Optional, Sequence, Tuple

from aiohttp import ClientSession

from eve_esi.app_config import SCHEMA_URL
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

DEFAULT_CALLBACKS = {
    "success": [ResponseToJson(), LogSuccess()],
    "retry": [LogRetry()],
    "fail": [LogFail],
}


def get_schema():
    action: AiohttpAction = AiohttpAction(
        method="get",
        url_template=SCHEMA_URL,
        action_callbacks=DEFAULT_CALLBACKS,
    )
    return action


class EsiProvider:
    """
    # TODO param validation
    # TODO default callbacks


    [extended_summary]
    """

    def __init__(self, schema):
        self.schema = schema
        self.lookup_table = self.make_lookup_table(self.schema)

    def make_lookup_table(self, schema):
        lookup = {}
        for path, path_schema in schema["paths"].items():
            for method, method_schema in path_schema.items():
                lookup_key = method_schema["operationId"]
                lookup[lookup_key] = {
                    "method": method,
                    "path": path,
                }
        return lookup

    def make_url_template(self, path: str) -> str:
        return path.replace("{", "${")

    def lookup_path(self, op_id) -> Tuple[str, str]:
        data = self.lookup_table.get(op_id, None)
        if data is None:
            raise NotImplementedError(f"missing data for {op_id}")
        method = data["method"]
        # TODO handle route version changes
        path = "https://" + self.schema["host"] + self.schema["basePath"] + data["path"]
        return (method, path)

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
    ) -> AiohttpAction:
        method, path = self.lookup_path(op_id)
        url_template = self.make_url_template(path)
        if not self.validate_params(op_id, path_params, query_params):
            raise NotImplementedError(
                "Error validating params, this should be move to validation function."
            )
        request_kwargs = optional_object(request_kwargs, dict)
        if request_kwargs is not None:
            request_kwargs["params"] = query_params
        action = AiohttpAction(
            method,
            url_template,
            url_parameters=path_params,
            retry_limit=retry_limit,
            request_kwargs=request_kwargs,
            action_callbacks=action_callbacks,
            action_messengers=action_messengers,
        )
        return action
