"""Main module."""
import asyncio
from math import ceil
from typing import Dict, List, Optional, Sequence

from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.job_to_action import make_action_from_job
from eve_esi_jobs.model_helpers import pre_process_work_order
from eve_esi_jobs.models import EsiJob, EsiWorkOrder
from eve_esi_jobs.pfmsoft.util.async_actions.aiohttp import (
    AiohttpQueueWorker,
    do_aiohttp_action_queue,
)


def do_jobs(esi_jobs: Sequence[EsiJob], esi_provider: EsiProvider, worker_count=1):
    """ May mutate esi_jobs """
    workers = []
    for _ in range(worker_count):
        workers.append(AiohttpQueueWorker())
    actions = []
    for esi_job in esi_jobs:
        action = make_action_from_job(esi_job, esi_provider)
        actions.append(action)
    asyncio.run(do_aiohttp_action_queue(actions, workers))
    return esi_jobs


def do_work_order(
    ewo: EsiWorkOrder, esi_provider: EsiProvider, worker_count: Optional[int] = None
):
    pre_process_work_order(ewo)
    worker_count = get_worker_count(len(ewo.jobs), worker_count)
    do_jobs(ewo.jobs, esi_provider, worker_count)


def get_worker_count(job_count, worker_count: Optional[int]) -> int:
    max_workers = 100
    worker_calc = ceil(job_count / 10)
    if worker_calc > max_workers:
        worker_calc = max_workers
    if worker_count is not None:
        worker_calc = worker_count
    return worker_calc


def deserialize_json_job(esi_job_json: Dict) -> EsiJob:
    esi_job = EsiJob(**esi_job_json)
    return esi_job


def deserialize_json_work_order(esi_work_order_json: Dict) -> EsiWorkOrder:
    esi_work_order = EsiWorkOrder(**esi_work_order_json)
    return esi_work_order
