"""Main module."""
import asyncio
import logging
from math import ceil
from typing import Any, Dict, List, Optional, Sequence

from pfmsoft.aiohttp_queue import AiohttpQueueWorker
from pfmsoft.aiohttp_queue.aiohttp import ActionObserver
from pfmsoft.aiohttp_queue.runners import queue_runner

from eve_esi_jobs.callback_manifest import CallbackManifest, new_manifest
from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.helpers import optional_object
from eve_esi_jobs.job_preprocessor import JobPreprocessor
from eve_esi_jobs.job_to_action import JobsToActions
from eve_esi_jobs.models import EsiJob, EsiWorkOrder

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def do_jobs(
    esi_jobs: Sequence[EsiJob],
    esi_provider: EsiProvider,
    callback_manifest: Optional[CallbackManifest] = None,
    jobs_to_actions: Optional[JobsToActions] = None,
    workorder_attributes: Optional[Dict[str, Any]] = None,
    observers: Optional[List[ActionObserver]] = None,
    worker_count: Optional[int] = None,
    max_workers: int = 100,
) -> Sequence[EsiJob]:
    callback_manifest = optional_object(
        callback_manifest, CallbackManifest.manifest_factory
    )
    jobs_to_actions = optional_object(jobs_to_actions, JobsToActions)
    workorder_attributes = optional_object(workorder_attributes, dict)
    observers = optional_object(observers, list)
    if worker_count is None:
        worker_count = get_worker_count(len(esi_jobs), max_workers)
    workers = []
    for _ in range(worker_count):
        workers.append(AiohttpQueueWorker())
    job_preprocessor = JobPreprocessor()
    for esi_job in esi_jobs:
        esi_job.update_attributes(workorder_attributes)
        job_preprocessor.pre_process_job(esi_job)
    actions = jobs_to_actions.make_actions(
        esi_jobs=esi_jobs,
        esi_provider=esi_provider,
        callback_manifest=callback_manifest,
        observers=observers,
    )
    asyncio.run(queue_runner(actions, workers))
    return esi_jobs


def do_workorder(
    ewo: EsiWorkOrder,
    esi_provider: EsiProvider,
    worker_count: Optional[int] = None,
    callback_manifest: Optional[CallbackManifest] = None,
    jobs_to_actions: Optional[JobsToActions] = None,
    observers: Optional[List[ActionObserver]] = None,
    max_workers: int = 100,
) -> EsiWorkOrder:
    callback_manifest = optional_object(
        callback_manifest, CallbackManifest.manifest_factory
    )
    jobs_to_actions = optional_object(jobs_to_actions, JobsToActions)
    if worker_count is None:
        worker_count = get_worker_count(len(ewo.jobs), max_workers)
    do_jobs(
        esi_jobs=ewo.jobs,
        esi_provider=esi_provider,
        callback_manifest=callback_manifest,
        jobs_to_actions=jobs_to_actions,
        workorder_attributes=ewo.attributes(),
        observers=observers,
        worker_count=worker_count,
    )
    return ewo


def get_worker_count(job_count, max_workers: int = 100) -> int:
    """Try to strike a reasonable balance between speed and DOS."""
    worker_calc = ceil(job_count / 2)
    if worker_calc > max_workers:
        worker_calc = max_workers
    return worker_calc
