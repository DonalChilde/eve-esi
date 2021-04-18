"""Main module."""
import asyncio
import json
import logging
from math import ceil
from typing import Any, Dict, List, Optional, Sequence

import yaml
from pfmsoft.aiohttp_queue import AiohttpQueueWorker
from pfmsoft.aiohttp_queue.aiohttp import ActionObserver
from pfmsoft.aiohttp_queue.runners import queue_runner

from eve_esi_jobs.callback_manifest import CallbackManifest, new_manifest
from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.helpers import combine_dictionaries, optional_object
from eve_esi_jobs.job_to_action import JobsToActions
from eve_esi_jobs.model_helpers import JobPreprocessor
from eve_esi_jobs.models import EsiJob, EsiWorkOrder, JobCallback

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
    callback_manifest = optional_object(callback_manifest, new_manifest)
    jobs_to_actions = optional_object(jobs_to_actions, JobsToActions)
    workorder_attributes = optional_object(workorder_attributes, dict)
    observers = optional_object(observers, list)
    worker_count = get_worker_count(len(esi_jobs), worker_count, max_workers)
    workers = []
    for _ in range(worker_count):
        workers.append(AiohttpQueueWorker())
    # jobs_to_actions = JobsToActions()
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


def do_work_order(
    ewo: EsiWorkOrder,
    esi_provider: EsiProvider,
    worker_count: Optional[int] = None,
    callback_manifest: Optional[CallbackManifest] = None,
    jobs_to_actions: Optional[JobsToActions] = None,
    observers: Optional[List[ActionObserver]] = None,
    max_workers: int = 100,
) -> EsiWorkOrder:
    callback_manifest = optional_object(callback_manifest, new_manifest)
    jobs_to_actions = optional_object(jobs_to_actions, JobsToActions)
    # additional_attributes = optional_object(additional_attributes, dict)
    # combined_attributes = combine_dictionaries(
    #     ewo.attributes(), [additional_attributes]
    # )
    # pre_processor = WorkOrderPreprocessor()
    # pre_processor.pre_process_work_order(ewo)
    worker_count = get_worker_count(len(ewo.jobs), worker_count, max_workers)
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


def get_worker_count(job_count, workers: Optional[int], max_workers: int = 100) -> int:
    """Try to strike a reasonable balance between speed and DOS."""
    worker_calc = ceil(job_count / 2)
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


def deserialize_job_from_string(esi_job_string: str, format_id: str = "json") -> EsiJob:
    if format_id.lower() == "json":
        job_dict = json.loads(esi_job_string)
    elif format_id.lower() == "yaml":
        job_dict = yaml.safe_load(esi_job_string)
    else:
        raise ValueError(
            f"Bad format_id argument. Got: {format_id} expected one of {['json','yaml']}"
        )
    esi_job = deserialize_job_from_dict(job_dict)
    return esi_job


def deserialize_work_order_from_string(
    esi_work_order_string: str, format_id: str = "json"
) -> EsiWorkOrder:
    if format_id.lower() == "json":
        ewo_dict = json.loads(esi_work_order_string)
    elif format_id.lower() == "yaml":
        ewo_dict = yaml.safe_load(esi_work_order_string)
    else:
        raise ValueError(
            f"Bad format_id argument. Got: {format_id} expected one of {['json','yaml']}"
        )
    esi_work_order = deserialize_work_order_from_dict(ewo_dict)
    return esi_work_order


def serialize_job(esi_job: EsiJob, format_id: str = "json") -> str:
    serialized_json = esi_job.json(exclude_defaults=True, indent=2)
    if format_id.lower() == "json":
        return serialized_json
    if format_id.lower() == "yaml":
        json_rep = json.loads(serialized_json)
        serialized_yaml = yaml.dump(json_rep)
        return serialized_yaml
    raise ValueError(
        f"Bad format_id argument. Got: {format_id} expected one of {['json','yaml']}"
    )


def serialize_work_order(ewo: EsiWorkOrder, format_id: str = "json") -> str:
    serialized_json = ewo.json(exclude_defaults=True, indent=2)
    if format_id.lower() == "json":
        return serialized_json
    if format_id.lower() == "yaml":
        json_rep = json.loads(serialized_json)
        serialized_yaml = yaml.dump(json_rep)
        return serialized_yaml
    raise ValueError(
        f"Bad format_id argument. Got: {format_id} expected one of {['json','yaml']}"
    )


def job_to_dict(esi_job: EsiJob) -> Dict:
    return esi_job.dict()


def work_order_to_dict(ewo: EsiWorkOrder) -> Dict:
    return ewo.dict()
