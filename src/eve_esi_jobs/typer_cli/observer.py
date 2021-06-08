# from typing import Optional

# import typer
# from pfmsoft.aiohttp_queue import (
#     ActionObserver,
#     ActionState,
#     AiohttpAction,
#     AiohttpActionCallback,
# )

# from eve_esi_jobs.models import EsiJob


# class EsiObserver(ActionObserver):
#     def __init__(self) -> None:
#         super().__init__()

#     def update(
#         self,
#         action: AiohttpAction,
#         source: str,
#         msg: str,
#         **kwargs,
#     ):
#         _ = kwargs
#         esi_job: EsiJob = action.context.get("esi_job", None)
#         if action.state == ActionState.FAIL:
#             if esi_job is None:
#                 typer.echo(
#                     f"Failed action for unknown job. {action} status code="
#                     f"{action.response.status}, reason={action.response.reason}"
#                     f"url={action.response.url}\n"
#                 )
#             typer.echo(
#                 f"Failed <{esi_job.__class__.__name__} name={esi_job.name}, "
#                 f"op_id={esi_job.op_id}>, {action} status code="
#                 f"{action.response.status}, reason={action.response.reason}, "
#                 f"url={action.response.url}\n"
#             )
#             return
#         if action.state == ActionState.CALLBACK_FAIL:
#             typer.echo(
#                 f"Uncertain Result: <{esi_job.__class__.__name__} name={esi_job.name}, "
#                 f"op_id={esi_job.op_id}>, {action} status code="
#                 f"{action.response.status}, reason={action.response.reason}, "
#                 f"url={action.response.url}, source={source} msg={msg}\n"
#             )
#             return
