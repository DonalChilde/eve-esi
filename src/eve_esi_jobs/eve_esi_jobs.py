"""Main module."""
import asyncio
import logging
from math import ceil
from typing import Dict, Optional, Sequence

from pfmsoft.aiohttp_queue import AiohttpQueueWorkerFactory
from pfmsoft.aiohttp_queue.runners import queue_runner

from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.job_to_action import make_action_from_job
from eve_esi_jobs.model_helpers import pre_process_work_order
from eve_esi_jobs.models import EsiJob, EsiWorkOrder

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def do_jobs(
    esi_jobs: Sequence[EsiJob],
    esi_provider: EsiProvider,
    template_overrides: Dict,
    worker_count: Optional[int] = None,
    max_workers: int = 100,
):
    worker_count = get_worker_count(len(esi_jobs), worker_count, max_workers)
    factories = []
    for _ in range(worker_count):
        factories.append(AiohttpQueueWorkerFactory())
    actions = []
    for esi_job in esi_jobs:
        action = make_action_from_job(esi_job, esi_provider, template_overrides)
        actions.append(action)
    asyncio.run(queue_runner(actions, factories))
    return esi_jobs


def do_work_order(
    ewo: EsiWorkOrder,
    esi_provider: EsiProvider,
    worker_count: Optional[int] = None,
    max_workers: int = 100,
):
    pre_process_work_order(ewo)
    worker_count = get_worker_count(len(ewo.jobs), worker_count, max_workers)
    do_jobs(ewo.jobs, esi_provider, ewo.get_template_overrides(), worker_count)


def get_worker_count(job_count, workers: Optional[int], max_workers: int = 100) -> int:
    """Try to strike a reasonable balance between speed and DOS."""
    worker_calc = ceil(job_count / 10)
    if worker_calc > max_workers:
        worker_calc = max_workers
    if workers is not None:
        worker_calc = workers
    return worker_calc


def deserialize_json_job(esi_job_json: Dict) -> EsiJob:
    esi_job = EsiJob(**esi_job_json)
    return esi_job


def deserialize_json_work_order(esi_work_order_json: Dict) -> EsiWorkOrder:
    esi_work_order = EsiWorkOrder(**esi_work_order_json)
    return esi_work_order


def serialize_job(esi_job: EsiJob) -> Dict:
    serialized = esi_job.dict()
    return serialized


def serialize_work_order(ewo: EsiWorkOrder) -> Dict:
    serialized = ewo.dict()
    return serialized
