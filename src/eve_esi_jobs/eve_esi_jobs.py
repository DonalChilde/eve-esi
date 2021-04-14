"""Main module."""
import asyncio
import json
import logging
from math import ceil
from typing import Any, Dict, Optional, Sequence

from pfmsoft.aiohttp_queue import AiohttpQueueWorkerFactory
from pfmsoft.aiohttp_queue.runners import queue_runner

from eve_esi_jobs.callback_manifest import CallbackProvider
from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.helpers import combine_dictionaries, optional_object
from eve_esi_jobs.job_to_action import JobsToActions
from eve_esi_jobs.model_helpers import WorkOrderPreprocessor
from eve_esi_jobs.models import EsiJob, EsiWorkOrder

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def do_jobs(
    esi_jobs: Sequence[EsiJob],
    esi_provider: EsiProvider,
    callback_provider: Optional[CallbackProvider] = None,
    jobs_to_actions: Optional[JobsToActions] = None,
    additional_attributes: Optional[Dict[str, Any]] = None,
    worker_count: Optional[int] = None,
    max_workers: int = 100,
) -> Sequence[EsiJob]:
    callback_provider = optional_object(callback_provider, CallbackProvider)
    jobs_to_actions = optional_object(jobs_to_actions, JobsToActions)
    additional_attributes = optional_object(additional_attributes, dict)
    worker_count = get_worker_count(len(esi_jobs), worker_count, max_workers)
    factories = []
    for _ in range(worker_count):
        factories.append(AiohttpQueueWorkerFactory())
    # jobs_to_actions = JobsToActions()
    actions = jobs_to_actions.make_actions(
        esi_jobs, esi_provider, callback_provider, additional_attributes
    )
    asyncio.run(queue_runner(actions, factories))
    return esi_jobs


def do_work_order(
    ewo: EsiWorkOrder,
    esi_provider: EsiProvider,
    worker_count: Optional[int] = None,
    callback_provider: Optional[CallbackProvider] = None,
    jobs_to_actions: Optional[JobsToActions] = None,
    additional_attributes: Optional[Dict[str, Any]] = None,
    max_workers: int = 100,
) -> EsiWorkOrder:
    callback_provider = optional_object(callback_provider, CallbackProvider)
    jobs_to_actions = optional_object(jobs_to_actions, JobsToActions)
    additional_attributes = optional_object(additional_attributes, dict)
    combined_attributes = combine_dictionaries(
        ewo.attributes(), [additional_attributes]
    )
    pre_processor = WorkOrderPreprocessor()
    pre_processor.pre_process_work_order(ewo)
    worker_count = get_worker_count(len(ewo.jobs), worker_count, max_workers)
    do_jobs(
        ewo.jobs,
        esi_provider,
        callback_provider,
        jobs_to_actions,
        combined_attributes,
        worker_count,
    )
    return ewo


def get_worker_count(job_count, workers: Optional[int], max_workers: int = 100) -> int:
    """Try to strike a reasonable balance between speed and DOS."""
    worker_calc = ceil(job_count / 10)
    if worker_calc > max_workers:
        worker_calc = max_workers
    if workers is not None:
        worker_calc = workers
    return worker_calc


def deserialize_job_from_dict(esi_job_dict: Dict) -> EsiJob:
    esi_job = EsiJob(**esi_job_dict)
    return esi_job


def deserialize_work_order_from_dict(esi_work_order_dict: Dict) -> EsiWorkOrder:
    esi_work_order = EsiWorkOrder(**esi_work_order_dict)
    return esi_work_order


def deserialize_job_from_string(esi_job_string: str) -> EsiJob:
    job_dict = json.loads(esi_job_string)
    esi_job = deserialize_job_from_dict(job_dict)
    return esi_job


def deserialize_work_order_from_string(esi_work_order_string: str) -> EsiWorkOrder:
    ewo_dict = json.loads(esi_work_order_string)
    esi_work_order = deserialize_work_order_from_dict(ewo_dict)
    return esi_work_order


def serialize_job(esi_job: EsiJob) -> str:
    serialized = esi_job.json(exclude_defaults=True, indent=2)
    return serialized


def serialize_work_order(ewo: EsiWorkOrder) -> str:
    serialized = ewo.json(exclude_defaults=True, indent=2)
    return serialized


def job_to_dict(esi_job: EsiJob) -> Dict:
    return esi_job.dict()


def work_order_to_dict(ewo: EsiWorkOrder) -> Dict:
    return ewo.dict()
