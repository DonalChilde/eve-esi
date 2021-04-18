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
                    f"Failed action for unknown job. {action} status code: "
                    f"{action.response.status}, {action.response.reason}"
                    "See log for details."
                )
            typer.echo(
                f"Failed job: {esi_job.name}, {action} status code: "
                f"{action.response.status}, {action.response.reason}"
                "See log for details."
            )
            return
        if action.state == ActionState.CALLBACK_FAIL:
            if callback is not None:
                typer.echo(
                    f"Uncertain Result: A callback failed for job {esi_job.name} "
                    f"during {action} with msg: {callback.state_message} "
                    "See log for details."
                )
                return
            typer.echo(
                f"Uncertain Result: A callback failed for job {esi_job.name} "
                f"during {action} for unreported reasons. See log for details."
            )
