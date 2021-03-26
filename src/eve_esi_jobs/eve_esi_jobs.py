"""Main module."""
import asyncio
from typing import Dict, List, Sequence

from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.job_to_action import make_action_from_job
from eve_esi_jobs.model_helpers import deserialize_json_job
from eve_esi_jobs.models import EsiJob
from eve_esi_jobs.pfmsoft.util.async_actions.aiohttp import (
    AiohttpQueueWorker,
    do_aiohttp_action_queue,
)


def do_jobs(esi_jobs: Sequence[EsiJob], esi_provider: EsiProvider, worker_count=1):
    """ Mutates esi_jobs """
    workers = []
    for _ in range(worker_count):
        workers.append(AiohttpQueueWorker())
    actions = []
    for esi_job in esi_jobs:
        action = make_action_from_job(esi_job, esi_provider)
        # action.context["esi_job"] = esi_job
        actions.append(action)
    asyncio.run(do_aiohttp_action_queue(actions, workers))
    return esi_jobs


def do_jobs_json(
    esi_jobs_json: List[Dict], esi_provider: EsiProvider, worker_count=1
) -> Sequence[EsiJob]:
    esi_jobs: List[EsiJob] = []
    for esi_job_json in esi_jobs_json:
        esi_job = deserialize_json_job(esi_job_json)
        esi_jobs.append(esi_job)
        do_jobs(esi_jobs, esi_provider, worker_count)
    return esi_jobs
