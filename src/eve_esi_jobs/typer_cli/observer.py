from typing import Optional

import typer
from pfmsoft.aiohttp_queue import (
    ActionObserver,
    ActionState,
    AiohttpAction,
    AiohttpActionCallback,
)

from eve_esi_jobs.models import EsiJob


class EsiObserver(ActionObserver):
    def __init__(self) -> None:
        super().__init__()

    def update(
        self,
        action: AiohttpAction,
        callback: Optional[AiohttpActionCallback] = None,
        **kwargs,
    ):
        _ = kwargs
        esi_job: EsiJob = action.context.get("esi_job", None)
        if action.state == ActionState.FAIL:

            if esi_job is None:
                typer.echo(
                    f"Failed action for unknown job. {action} status code="
                    f"{action.response.status}, reason={action.response.reason}\n"
                )
            typer.echo(
                f"Failed <{esi_job.__class__.__name__} name={esi_job.name}>, "
                f"{action} status code="
                f"{action.response.status}, reason={action.response.reason}\n"
            )
            return
        if action.state == ActionState.CALLBACK_FAIL:
            if callback is not None:
                typer.echo(
                    f"Uncertain Result: {callback.__class__.__name__} failed with "
                    f"msg: {callback.state_message} for <{esi_job.__class__.__name__} name={esi_job.name}> "
                    f"during {action} \n"
                )
                return
            typer.echo(
                f"Uncertain Result: {callback.__class__.__name__} failed for "
                f"<{esi_job.__class__.__name__} name={esi_job.name}>  "
                f"during {action} for unreported reasons. \n"
            )
