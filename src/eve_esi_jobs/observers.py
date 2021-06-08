import logging
from typing import List, Optional

from eve_esi_jobs.models import EsiJob, EsiJobResult

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class QueueObserver:
    def __init__(self) -> None:
        pass

    # FIXME needs to report list of exceptions.

    def update(
        self,
        worker,
        job: EsiJob,
        result: Optional[EsiJobResult] = None,
        msg: str = "",
        exceptions: Optional[List[Exception]] = None,
        **kwargs,
    ):
        _, _ = kwargs, worker
        print(result, job, msg)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(" ")"


class LoggingObserver(QueueObserver):
    def __init__(self) -> None:
        super().__init__()

    def update(
        self,
        worker,
        job: EsiJob,
        result: Optional[EsiJobResult] = None,
        msg: str = "",
        exceptions: Optional[List[Exception]] = None,
        **kwargs,
    ):
        logger.debug(
            "Worker: %r, job: %r, result: %r, msg: %s, exceptions: %s, kwargs: %r",
            worker,
            str(job)[:500],
            str(result)[:500],
            msg,
            exceptions,
            kwargs,
        )
